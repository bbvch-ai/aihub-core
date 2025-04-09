from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import AgentInTheLoop, StopEvent, UserMessageEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.prompts.rich import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.GroundedAgent.GroundedAgentConfig import GroundedAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientEvent import ContextInsufficientEvent
from aihub_agent.agents.RagAgent.events.ContextSufficientEvent import ContextSufficientEvent
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    return isinstance(event.stop_event, AnswerStopEvent)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    return isinstance(event.stop_event, NoAnswerStopEvent)


class GroundedAgent(Agent):
    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: GroundedAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RouterEvent:
        await displayer.display_thought("Routing to determine if the context is sufficient.")

        instructions = RichPromptTemplate(
            template_str=t("lib.prompt.router.instructions.context_sufficient"),
        ).format(chat_history=event.messages[:-1], query=event.messages[-1].content)

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await route_to_event_using_llm(
                instructions=instructions,
                routes=[
                    RouteOptions.for_event(
                        ContextSufficientEvent(), "Choose this option if the context is sufficient."
                    ),
                    RouteOptions.for_event(
                        ContextInsufficientEvent(reasoning=""), "Choose this option if the context is NOT sufficient."
                    ),
                ],
                t=t,
                llm=llm,
            )

    @step()
    async def router_step(
        self,
        displayer: EventDisplayer,
        router_event: RouterEvent,
    ) -> ContextSufficientEvent | ContextInsufficientEvent:
        await displayer.display_thought(router_event.reason)
        return router_event.selected_option.event

    @step()
    async def respond_step(
        self,
        agent_config: GroundedAgentConfig,
        displayer: EventDisplayer,
        event: UserMessageEvent,
        _: ContextSufficientEvent,
    ):
        await displayer.display_thought("Context is sufficient, generating response now")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step()
    async def reject_step(
        self,
        user_message_event: UserMessageEvent,
        _: ContextInsufficientEvent,
        displayer: EventDisplayer,
        agent_config: GroundedAgentConfig,
    ) -> AgentInTheLoop.request:
        await displayer.display_thought("Context is NOT sufficient, asking expert")
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_asking_agent_class,
            agent_id=agent_config.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.messages[-1].content,
                locale=user_message_event.locale,
                user=user_message_event.user,
            ),
        )

    @step(precondition=is_answer_response)
    async def expert_answered_step(self, displayer: EventDisplayer, event: AgentInTheLoop.response):
        await displayer.display_chunk(event.stop_event.expert_answer, model_name="expert")
        return StopEvent()

    @step(precondition=is_no_answer_response)
    async def expert_not_answered_step(self, displayer: EventDisplayer, event: AgentInTheLoop.response):
        await displayer.display_chunk("Expert was not able to answer question, apologies.", model_name="expert")
        return StopEvent()

    @step()
    async def expert_exception_step(self, displayer: EventDisplayer, event: AgentInTheLoop.exception):
        await displayer.display_chunk("There was an exception interacting with the expert.", model_name="expert")
        return StopEvent()
