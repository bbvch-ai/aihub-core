from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, HumanInTheLoop, LLMStopEvent, StopEvent, UserMessageEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.nats.workflow.decorators.precondition import precondition
from aihub_lib.nats.workflow.decorators.step import step
from llama_index.core.prompts.rich import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertGroundedAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgentConfig import ExpertGroundedAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientEvent import ContextInsufficientEvent
from aihub_agent.agents.RagAgent.events.ContextSufficientEvent import ContextSufficientEvent


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer"""
    return isinstance(event.stop_event, AnswerStopEvent)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a unsuccessful answer"""
    return isinstance(event.stop_event, NoAnswerStopEvent)


class ExpertGroundedAgent(Agent):
    """
    This Agent grounds all its answers in the available context information and refused to answer
    questions that require knowledge not available in either the context or the past conversation
    history.
    Upon missing knowledge, the agent prompts the user that an expert in the matter could be
    contacted to acquire the missing knowledge.
    Note that this agent does NOT store the answer from the expert asking agent, only forwards
    the answer to the questioner.
    """

    @step(
        name=LocaleString(en="Start"),
        description=LocaleString(en="Processes messages sent by the user."),
        icon="line-md:chat",
    )
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: ExpertGroundedAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RouterEvent:
        chat_history = event.messages[:-1]
        user_query = event.messages[-1].content

        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_asked", user_query=user_query))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.need_to_determine_context"))

        instructions = RichPromptTemplate(
            template_str=t("lib.prompt.router.instructions.context_sufficient"),
        ).format(chat_history=chat_history, query=user_query)

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

    @step(
        name=LocaleString(en="Context Router"),
        description=LocaleString(en="Determines whether the context is sufficient to fulfill the users query."),
        icon="iconoir:missing-font",
    )
    async def context_sufficient_router_step(
        self,
        displayer: EventDisplayer,
        router_event: RouterEvent,
    ) -> ContextSufficientEvent | ContextInsufficientEvent:
        await displayer.display_thought(router_event.reason)
        return router_event.selected_option.event

    @step(
        name=LocaleString(en="Answer Question"),
        description=LocaleString(en="Users query can be safely fulfilled."),
        icon="simple-icons:answer",
    )
    async def answer_question_step(
        self,
        agent_config: ExpertGroundedAgentConfig,
        displayer: EventDisplayer,
        event: UserMessageEvent,
        _: ContextSufficientEvent,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.can_answer_question"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages, as_stop_step=True)

    @step(
        name=LocaleString(en="Ask for Consent"),
        description=LocaleString(en="Ask user for consent to contact expert with their question."),
        icon="akar-icons:chat-approve",
    )
    async def insufficient_context_step(
        self,
        _: ContextInsufficientEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.request:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.context_not_sufficient"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.asking_for_consent"))
        return HumanInTheLoop.invoke(question=t("agent.expert_grounded_agent.messages.consent_question"))

    @step(
        name=LocaleString(en="Consent Answer"),
        description=LocaleString(en="User answered the question for consent."),
        icon="carbon:question-answering",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserRequestsExpertEvent | StopEvent:
        if "yes" in event.response.lower() or "ja" in event.response.lower():
            await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_consented"))
            return UserRequestsExpertEvent()
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_declined"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.waiting_for_instructions"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.user_declined_confirmation"), model_name="gpt-4o"
        )

        return StopEvent()

    @step(
        name=LocaleString(en="Invoke ExpertAskingAgent"),
        description=LocaleString(en="Forwarding request to ExpertAskingAgent that will prompt experts."),
        icon="hugeicons:robot-02",
    )
    async def forward_to_expert_asking_agent_step(
        self,
        user_message_event: UserMessageEvent,
        _: UserRequestsExpertEvent,
        displayer: EventDisplayer,
        agent_config: ExpertGroundedAgentConfig,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_forwarding_confirmation"), model_name="expert"
        )
        await displayer.display_chunk("\n", model_name="expert")
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_answer_coming_soon"), model_name="expert"
        )
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_asking_agent_class,
            agent_id=agent_config.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.messages[-1].content,
                locale=user_message_event.locale,
                user=user_message_event.user,
            ),
        )

    @step(
        precondition=is_answer_response,
        name=LocaleString(en="Expert Answer Positive"),
        description=LocaleString(en="ExpertAskingAgent was able to extract information from expert."),
        icon="ix:user-success-filled",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.forwarding_expert_info"))
        await displayer.display_chunk(event.stop_event.expert_answer, model_name="expert")
        return StopEvent()

    @step(
        precondition=is_no_answer_response,
        name=LocaleString(en="Expert Answer Negative"),
        description=LocaleString(en="ExpertAskingAgent was NOT able to extract information from expert."),
        icon="ix:user-fail-filled",
    )
    async def expert_not_answered_step(
        self,
        displayer: EventDisplayer,
        _: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_unable_to_answer"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_unable_to_answer"), model_name="expert"
        )
        return StopEvent()

    @step(
        name=LocaleString(en="Expert Answer Error"),
        description=LocaleString(en="ExpertAskingAgent encountered an error."),
        icon="ix:error",
    )
    async def expert_exception_step(
        self,
        displayer: EventDisplayer,
        exception_event: AgentInTheLoop.exception,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(
            t(
                "agent.expert_grounded_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_error_occurred"), model_name="expert"
        )
        return StopEvent()
