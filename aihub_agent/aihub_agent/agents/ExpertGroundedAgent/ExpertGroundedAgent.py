from aihub_agent.agents.ExpertGroundedAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, StopEvent, UserMessageEvent, HumanInTheLoop
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.prompts.rich import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgentConfig import ExpertGroundedAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientEvent import ContextInsufficientEvent
from aihub_agent.agents.RagAgent.events.ContextSufficientEvent import ContextSufficientEvent
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


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

        await displayer.display_thought(f"The user asked '{user_query}'.")
        await displayer.display_thought("I need to figure out whether I have sufficient information to answer this question.")

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
    ):
        await displayer.display_thought("I can safely answer the users question now.")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step(
        name=LocaleString(en="Ask for Consent"),
        description=LocaleString(en="Ask user for consent to contact expert with their question."),
        icon="akar-icons:chat-approve",
    )
    async def insufficient_context_step(
        self,
        _: ContextInsufficientEvent,
        displayer: EventDisplayer,
    ) -> HumanInTheLoop.request:
        await displayer.display_thought("Context is NOT sufficient. I see the potential of forwarding this question to an expert.")
        await displayer.display_thought("Asking user for their consent to forward this question to a group of selected experts.")
        return HumanInTheLoop.invoke(
            question="Mir fehlt leider das nötige Wissen, um diese Frage zu beantworten. Soll ich für dich das nötige Wissen bei einem Experten abholen und auf dich zurück kommen?"
        )

    @step(
        name=LocaleString(en="Consent Answer"),
        description=LocaleString(en="User answered the question for consent."),
        icon="carbon:question-answering",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.response,
        displayer: EventDisplayer,
    ) -> UserRequestsExpertEvent | StopEvent:
        if "yes" in event.response.lower() or "ja" in event.response.lower():
            await displayer.display_thought("The user has expressed their consent.")
            return UserRequestsExpertEvent()
        await displayer.display_thought("The user does not wish to forward the question to an expert.")
        await displayer.display_thought("Waiting for new instructions.")
        await displayer.display_chunk("Alles klar.", model_name="gpt-4o")

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
    ):
        await displayer.display_thought("Forwarding question to 'ExpertAskingAgent' and waiting for it to get back to me.")
        await displayer.display_chunk("Deine Frage wurde an ein Team von Experten weitergeleitet.\n", model_name="expert")
        await displayer.display_chunk("Sobald ein Experte die Frage beantworten konnte werde ich auf Sie zurück kommen.", model_name="expert")
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
    async def expert_answered_step(self, displayer: EventDisplayer, event: AgentInTheLoop.response):
        await displayer.display_thought("'ExpertAskingAgent' got back with an answer from the expert.")
        await displayer.display_thought("Forwarding information from expert to user.")
        await displayer.display_chunk(event.stop_event.expert_answer, model_name="expert")
        return StopEvent()

    @step(
        precondition=is_no_answer_response,
        name=LocaleString(en="Expert Answer Negative"),
        description=LocaleString(en="ExpertAskingAgent was NOT able to extract information from expert."),
        icon="ix:user-fail-filled",
    )
    async def expert_not_answered_step(self, displayer: EventDisplayer, _: AgentInTheLoop.response):
        await displayer.display_thought("'ExpertAskingAgent' was unable to find an expert that was able to answer users question.")
        await displayer.display_chunk("Expert was not able to answer question, apologies.", model_name="expert")
        return StopEvent()

    @step(
        name=LocaleString(en="Expert Answer Error"),
        description=LocaleString(en="ExpertAskingAgent encountered an error."),
        icon="ix:error",
    )
    async def expert_exception_step(self, displayer: EventDisplayer, exception_event: AgentInTheLoop.exception):
        await displayer.display_thought(f"'ExpertAskingAgent' got back with an error {exception_event.exception_event.http_status_code}: {exception_event.exception_event.message}.")
        await displayer.display_chunk("There was an exception interacting with the expert.", model_name="expert")
        return StopEvent()
