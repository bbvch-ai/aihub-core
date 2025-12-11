from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
    StopEvent,
)
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.events import (
    ContextInsufficientWithQueryEvent,
    InOrderNodeCombinerEvent,
    LimitChatHistoryWithContextEvent,
)
from aihub_agent.rag.steps import (
    execute_condense_standalone_question,
    execute_context_sufficient_guard,
    execute_few_shot_guard,
    execute_limit_chat_history,
    execute_limit_chat_history_with_context,
    execute_respond_with_llm,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def is_retrieval_success(event: AgentInTheLoop.response) -> bool:
    """Precondition to check if retrieval was successful."""
    return isinstance(event.stop_event, RetrievalResponseEvent)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Requires InOrderNodeCombinerEvent AND ContextSufficientAcceptEvent.
    """
    return context_sufficient_event is not None


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information
    via a shared RetrievalAgent, condense questions, and generate responses using a
    configured language model.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Delegates retrieval to RetrievalAgent via AgentInTheLoop.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: This is the simple RAG agent without expert escalation.
    For expert escalation support, use ExpertRAGAgent.
    """

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        """Truncates incoming chat messages to fit within the configured token limit."""
        return execute_limit_chat_history(
            messages=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        """Condenses the chat history and user query into a standalone question."""
        return await execute_condense_standalone_question(
            limited_history=event.limited_history,
            user_query=start_event.user_query,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            condense_prompt=agent_config.condense_question_prompt,
        )

    @step(
        name=LocaleString(en="Few Shot Guard"),
        description=LocaleString(en="Guards the question to ensure it is appropriate for the agent to answer."),
    )
    async def few_shot_guard_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        """Guards the question to ensure it is appropriate for the agent to answer."""
        return await execute_few_shot_guard(
            condensed_question=event.condensed_chat_message.content,
            few_shot_examples=agent_config.few_shot_guard_examples,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
        )

    @step(
        name=LocaleString(en="Invoke Retrieval Agent"),
        description=LocaleString(en="Delegates retrieval to the shared RetrievalAgent."),
        icon="hugeicons:robot-02",
    )
    async def invoke_retrieval_agent_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Invokes the RetrievalAgent to retrieve relevant nodes."""
        await displayer.display_thought(t("agent.thought.searching_knowledge"))

        if isinstance(event, StandaloneQuestionCondenserEvent):
            query = event.condensed_chat_message.content
        else:
            query = event.new_query

        return AgentInTheLoop.invoke(
            agent_class=agent_config.retrieval_agent_class,
            agent_id=agent_config.retrieval_agent_id,
            start_event=QuestionStartEvent(
                question=query,
                locale=start_event.locale,
            ),
        )

    @step(
        name=LocaleString(en="Retrieval Complete"),
        description=LocaleString(en="Processes the successful retrieval response."),
        precondition=is_retrieval_success,
    )
    async def retrieval_complete_step(
        self,
        event: AgentInTheLoop.response,
    ) -> InOrderNodeCombinerEvent:
        """Processes the successful retrieval response from RetrievalAgent."""
        retrieval_response: RetrievalResponseEvent = event.stop_event
        return InOrderNodeCombinerEvent(context_message=retrieval_response.context_message)

    @step(
        name=LocaleString(en="Retrieval Error"),
        description=LocaleString(en="Handles errors from the RetrievalAgent."),
    )
    async def retrieval_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handles errors from the RetrievalAgent."""
        await displayer.display_thought(
            t(
                "agent.rag_agent.thoughts.retrieval_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(t("agent.rag_agent.messages.retrieval_error"), model_name="RAG Agent")
        return StopEvent()

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: InOrderNodeCombinerEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        """Guards the context to ensure it is sufficient for generating a response."""
        return await execute_context_sufficient_guard(
            context_content=event.context_message.content or "",
            user_query=user_query_event.condensed_chat_message.content or "",
            check_context_sufficiency=agent_config.check_context_sufficiency or False,
            max_hops=agent_config.max_hops,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            run_context=run_context,
        )

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """Includes the combined context and truncates chat history again."""
        return execute_limit_chat_history_with_context(
            chat_history=chat_history_event.limited_history,
            context_message=context_event.context_message,
            last_user_message=start_event.last_user_message,
            llm_config=agent_config.llm,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )

    @step(
        name=LocaleString(en="Respond with LLM"),
        description=LocaleString(en="Generates a response using the configured LLM."),
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """Generates a response using the configured LLM."""
        if isinstance(event, FewShotRejectEvent | ContextInsufficientRejectEvent):
            messages = limited_history_without_context.limited_history
            reject_reason = event.reason
        else:
            messages = event.limited_history_with_context
            reject_reason = None

        return await execute_respond_with_llm(
            messages=messages,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            system_prompt=agent_config.system_prompt,
            reject_reason=reject_reason,
        )
