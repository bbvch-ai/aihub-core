from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import HumanInTheLoop, StopEvent, UserMessageEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole, ChatResponse
from llama_index.core.prompts import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerInsufficientEvent import ExpertAnswerInsufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerSufficientEvent import ExpertAnswerSufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.workflow.decorators.step import step


class ExpertAskingAgent(Agent):

    @step()
    async def start_asking_step(
        self,
        question_event: AskExpertStartEvent | AskExpertEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> HumanInTheLoop.request | NoAnswerStopEvent:
        await displayer.display_thought("I am expert agent!!!")

        loop_count = await run_context.get("loop_count")
        if loop_count < agent_config.loop_max:
            return NoAnswerStopEvent()

        chat_history = [ChatMessage(role=MessageRole.ASSISTANT, content=question_event.question_to_expert)]
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        return HumanInTheLoop.invoke(question=question_event.question_to_expert)

    @step()
    async def expert_response_step(
        self,
        initial_question_event: AskExpertStartEvent,
        expert_response_event: HumanInTheLoop.response,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> RouterEvent:
        await displayer.display_thought("Determine if expert answer is sufficient")

        loop_count = await run_context.get("loop_count")
        await run_context.set("loop_count", loop_count + 1)

        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]
        chat_history.append(ChatMessage(role=MessageRole.USER, content=expert_response_event.response))
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        instructions = RichPromptTemplate(
            template_str=t("lib.prompt.router.instructions.expert_answer_sufficient"),
        ).format(chat_history=chat_history, query=initial_question_event.question_to_expert)

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await route_to_event_using_llm(
                instructions=instructions,
                routes=[
                    RouteOptions.for_event(
                        ExpertAnswerSufficientEvent(),
                        "Choose this option if the experts response sufficiently answered the question.",
                    ),
                    RouteOptions.for_event(
                        ExpertAnswerInsufficientEvent(),
                        "Choose this option if the experts response does NOT sufficiently answered the question.",
                    ),
                ],
                t=t,
                llm=llm,
            )

    @step()
    async def router_step(
        self,
        router_event: RouterEvent,
    ) -> ExpertAnswerSufficientEvent | ExpertAnswerInsufficientEvent:
        return router_event.selected_option.event

    @step()
    async def finish_expert_flow(
        self,
        expert_response_event: HumanInTheLoop.response,
        initial_question_event: AskExpertStartEvent,
        _: ExpertAnswerSufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        run_context: RunContext,
    ) -> AnswerStopEvent:
        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(
                template_str=t("lib.expert_asking_agent.follow_up_question")
            ).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
            )
            response: ChatResponse = await llm.achat(chat)
        return AnswerStopEvent(expert_answer=response.message.content)

    @step()
    async def follow_up_question(
        self,
        router_event: RouterEvent,
        initial_question_event: AskExpertStartEvent,
        _: ExpertAnswerInsufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        run_context: RunContext,
    ) -> AskExpertEvent:
        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(
                template_str=t("lib.expert_asking_agent.follow_up_question")
            ).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
                reason=router_event.reason
            )
            response: ChatResponse = await llm.achat(chat)
            return AskExpertEvent(question_to_expert=response.message.content)
