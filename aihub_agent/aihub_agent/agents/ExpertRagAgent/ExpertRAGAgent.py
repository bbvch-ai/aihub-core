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
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.ExpertRagAgent.events.ExpertAnswerContextEvent import ExpertAnswerContextEvent
from aihub_agent.agents.ExpertRagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
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
    execute_order_nodes_by_documents,
    execute_rerank_nodes,
    execute_respond_with_llm,
    execute_retrieve,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled."""
    return isinstance(event, RetrieverEvent) and config.reranking_config.enabled


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    if not config.reranking_config.enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer."""
    return isinstance(event.stop_event, AnswerStopEvent)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful answer."""
    return isinstance(event.stop_event, NoAnswerStopEvent)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when:
    - ExpertAnswerContextEvent is present (expert flow), OR
    - InOrderNodeCombinerEvent is present AND ContextSufficientAcceptEvent is present (normal RAG flow)
    """
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    # For InOrderNodeCombinerEvent, we need ContextSufficientAcceptEvent
    return context_sufficient_event is not None


class ExpertRAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent with mandatory expert escalation.

    The ExpertRAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses. When context is insufficient, it automatically
    offers expert escalation to human experts.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Check context sufficiency and escalate to experts when needed.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: This agent requires expert_escalation configuration.
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
        event: UserMessageEvent,
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
        start_event: UserMessageEvent,
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
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        if isinstance(event, StandaloneQuestionCondenserEvent):
            query = event.condensed_chat_message.content
        else:
            query = event.new_query

        return await execute_retrieve(
            query=query,
            retrievers=agent_config.retrievers,
            displayer=displayer,
            t=t,
        )

    @step(
        name=LocaleString(en="Rerank Retrieved Nodes"),
        description=LocaleString(
            en="Reranks retrieved documents using a dedicated reranking model for improved relevance"
        ),
        icon="iconoir:sort-desc",
        precondition=reranking_enabled,
    )
    async def rerank_nodes_step(
        self,
        event: RetrieverEvent,
        condense_event: StandaloneQuestionCondenserEvent,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RerankerEvent:
        """Reranks retrieved documents using a dedicated reranking model."""
        return await execute_rerank_nodes(
            nodes=event.nodes,
            query=condense_event.condensed_chat_message.content,
            reranking_model=agent_config.reranking_config.reranking_model,
            displayer=displayer,
            t=t,
            reranking_enabled=agent_config.reranking_config.enabled,
        )

    @step(
        name=LocaleString(en="Order Nodes by Documents"),
        description=LocaleString(en="Orders the retrieved nodes by their source documents."),
        precondition=reranking_complete_or_disabled,
    )
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent | RerankerEvent,
        t: LocaleHandler,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        """Orders the retrieved nodes based on their source documents."""
        nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
        return await execute_order_nodes_by_documents(
            nodes=nodes,
            t=t,
            displayer=displayer,
            context_prompt=agent_config.context_prompt,
        )

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: ExpertRAGAgentConfig,
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
        return HumanInTheLoop.confirmation.invoke(question=t("agent.expert_grounded_agent.messages.consent_question"))

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
        user_message_event: UserMessageEvent,
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
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_escalation.expert_asking_agent_class,
            agent_id=agent_config.expert_escalation.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.user_query,
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
    ) -> ExpertAnswerContextEvent:
        """Processes successful expert response and formats it as context."""
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.can_answer_question"))

        # Format the expert conversation as context
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
        context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent,
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
        )
