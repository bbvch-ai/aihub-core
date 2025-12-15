from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    HumanInTheLoop,
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
    StopEvent,
)
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.insight import InsightCallerCredentials
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.ExpertRagAgent.events.ExpertAnswerContextEvent import ExpertAnswerContextEvent
from aihub_agent.agents.ExpertRagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_agent.agents.RagAgent.events import RAGUserMessageEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.events import (
    CombinedRetrievalEvent,
    ContextInsufficientWithQueryEvent,
    LimitChatHistoryWithContextEvent,
)
from aihub_agent.rag.preconditions import check_all_retrievals_complete, check_context_ready_for_history_limit
from aihub_agent.rag.steps import (
    execute_combine_retrieval_results,
    execute_condense_standalone_question,
    execute_context_sufficient_guard,
    execute_few_shot_guard,
    execute_invoke_retrieval,
    execute_limit_chat_history,
    execute_limit_chat_history_with_context,
    execute_respond_with_llm,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def all_retrievals_complete(
    retrieval_responses: list[AgentInTheLoop.response],
    agent_config: ExpertRAGAgentConfig,
) -> bool:
    """Precondition that waits for all retrieval agents to complete."""
    return check_all_retrievals_complete(retrieval_responses, len(agent_config.retrieval_agents))


@precondition()
async def is_expert_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful expert answer."""
    return isinstance(event.stop_event, AnswerStopEvent)


@precondition()
async def is_expert_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful expert answer."""
    return isinstance(event.stop_event, NoAnswerStopEvent)


@precondition()
async def context_ready_for_history_limit(
    context_event: CombinedRetrievalEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when:
    - ExpertAnswerContextEvent is present (expert flow), OR
    - CombinedRetrievalEvent is present AND ContextSufficientAcceptEvent is present (normal RAG flow)
    """
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    return check_context_ready_for_history_limit(context_sufficient_event)


class ExpertRAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent with mandatory expert escalation.

    The ExpertRAGAgent orchestrates steps to process user input, retrieve relevant information
    from multiple retrieval agents (any type), condense questions, and generate responses.
    When context is insufficient, it automatically offers expert escalation to human experts.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Multi-agent retrieval via any retrieval agent type (requires at least one insight retrieval agent).
    - Combined reranking of all retrieved nodes.
    - Check context sufficiency and escalate to experts when needed.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: This agent requires expert_escalation configuration and at least one insight retrieval agent.
    For a simple RAG without expert escalation, use RAGAgent.
    """

    # ==================== Core RAG Steps ====================

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
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
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        name=LocaleString(en="Invoke Retrieval Agents"),
        description=LocaleString(en="Invokes all configured retrieval agents (any type)."),
        icon="hugeicons:robot-02",
    )
    async def invoke_retrieval_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> list[AgentInTheLoop.request]:
        """Invokes all configured retrieval agents with unified RetrievalStartEvent.

        Note: ExpertRAGAgent requires at least one retrieval agent, so this always returns requests.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))

        query = (
            event.condensed_chat_message.content
            if isinstance(event, StandaloneQuestionCondenserEvent)
            else event.new_query
        )
        assert query is not None, "Query must not be None"

        override_lookup = start_event.retrieval_overrides if isinstance(start_event, RAGUserMessageEvent) else None

        return execute_invoke_retrieval(
            query=query,
            locale=start_event.locale,
            retrieval_agents=agent_config.retrieval_agents,
            retrieval_overrides=override_lookup,
        )

    @step(
        name=LocaleString(en="Combine Retrieval Results"),
        description=LocaleString(en="Combines results from all retrieval agents and applies reranking."),
        precondition=all_retrievals_complete,
    )
    async def combine_retrieval_results_step(
        self,
        agent_config: ExpertRAGAgentConfig,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        condenser_event: StandaloneQuestionCondenserEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
        retrieval_responses: list[AgentInTheLoop.response],
    ) -> CombinedRetrievalEvent:
        """Combines results from all retrieval agents and applies shared reranking."""
        return await execute_combine_retrieval_results(
            query=condenser_event.condensed_chat_message.content,
            locale=start_event.locale,
            t=t,
            displayer=displayer,
            retrieval_responses=retrieval_responses,
            reranking_enabled=agent_config.reranking_config.enabled,
            reranking_model=agent_config.reranking_config.reranking_model,
        )

    @step(
        name=LocaleString(en="Retrieval Error"),
        description=LocaleString(en="Handles errors from retrieval agents."),
    )
    async def retrieval_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handles errors from retrieval agents."""
        await displayer.display_thought(
            t(
                "agent.rag_agent.thoughts.retrieval_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(t("agent.rag_agent.messages.retrieval_error"), model_name="Expert RAG Agent")
        return StopEvent()

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: CombinedRetrievalEvent,
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

    # ==================== Expert Escalation Steps ====================

    @step(
        name=LocaleString(en="Handle Insufficient Context"),
        description=LocaleString(en="Handle insufficient context by asking for expert consent."),
        icon="akar-icons:chat-approve",
    )
    async def insufficient_context_ask_expert_step(
        self,
        _: ContextInsufficientRejectEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.confirmation.request:
        """Prompts user for consent to escalate to human expert."""
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.context_not_sufficient"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.asking_for_consent"))
        return HumanInTheLoop.confirmation.invoke(message=t("agent.expert_grounded_agent.messages.consent_question"))

    @step(
        name=LocaleString(en="Consent Answer"),
        description=LocaleString(en="User answered the question for consent."),
        icon="carbon:question-answering",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.confirmation.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserRequestsExpertEvent | ExpertRejectEvent:
        """Processes user consent or rejection for expert escalation."""
        if event.response is True:
            await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_consented"))
            return UserRequestsExpertEvent()
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_declined"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.waiting_for_instructions"))
        return ExpertRejectEvent(reason="User declined expert escalation")

    @step(
        name=LocaleString(en="Invoke ExpertAskingAgent"),
        description=LocaleString(en="Forwarding request to ExpertAskingAgent that will prompt experts."),
        icon="hugeicons:robot-02",
    )
    async def forward_to_expert_asking_agent_step(
        self,
        user_message_event: UserMessageEvent | RAGUserMessageEvent,
        _: UserRequestsExpertEvent,
        displayer: EventDisplayer,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Invokes ExpertAskingAgent to prompt human experts."""
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_forwarding_confirmation"), model_name="RAG Agent"
        )
        await displayer.display_chunk("\n", model_name="RAG Agent")
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_answer_coming_soon"), model_name="RAG Agent"
        )

        # Use caller's credentials if provided, otherwise use this agent's identity
        credentials = None
        if isinstance(user_message_event, RAGUserMessageEvent) and user_message_event.insight_caller_credentials:
            credentials = user_message_event.insight_caller_credentials
        else:
            credentials = InsightCallerCredentials(
                agent_class=agent_config.agent_class,
                agent_id=agent_config.agent_id,
            )

        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_escalation.expert_asking_agent_class,
            agent_id=agent_config.expert_escalation.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.user_query,
                locale=user_message_event.locale,
                user=user_message_event.user,
                write_insight_namespace=agent_config.write_insight_namespace,
                write_insight_credentials=credentials,
            ),
        )

    @step(
        precondition=is_expert_answer_response,
        name=LocaleString(en="Expert Answer Positive"),
        description=LocaleString(en="ExpertAskingAgent was able to extract information from expert."),
        icon="ix:user-success-filled",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> ExpertAnswerContextEvent:
        """Processes successful expert response and formats it as context."""
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.can_answer_question"))

        expert_conversation = event.stop_event.expert_conversation
        conversation_parts = []
        for msg in expert_conversation:
            role_label = "Agent" if msg.role == MessageRole.ASSISTANT else "Expert"
            content = msg.content or ""
            conversation_parts.append(f"{role_label}: {content}")
        expert_conversation_text = "\n".join(conversation_parts)

        context_content = t("agent.prompt.expert_context", expert_conversation=expert_conversation_text)
        await displayer.display_thought(f"Expert context: {context_content}")

        context_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=context_content,
        )
        return ExpertAnswerContextEvent(context_message=context_message)

    @step(
        precondition=is_expert_no_answer_response,
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
        """Handles case when expert was unable to provide an answer."""
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
        """Handles errors from ExpertAskingAgent."""
        await displayer.display_thought(
            t(
                "agent.expert_grounded_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_error_occurred"), model_name="RAG Agent"
        )
        return StopEvent()

    # ==================== Response Generation Steps ====================

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: CombinedRetrievalEvent | ExpertAnswerContextEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
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
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ExpertRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """Generates a response using the configured LLM."""
        if isinstance(event, FewShotRejectEvent | ExpertRejectEvent):
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
            context_insufficient_prompt=agent_config.context_insufficient_prompt,
        )
