from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AddMemoryToChatHistoryEvent,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    RAGFailureStopEvent,
    RAGStartEvent,
    RAGSuccessStopEvent,
    RerankerEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    StandaloneQuestionCondenserEvent,
    StoreUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    AgentMemory,
    LLMConfig,
    OrgMemoryNamespaceResolver,
    RetrievalRuntimeConfig,
    extend_chat_history_with_organization_memory,
    extend_chat_history_with_user_memory,
    narrow_retrievers,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.limit_chat_history_with_context_event import (
    LimitChatHistoryWithContextEvent,
)
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.rag.preconditions import (
    check_context_ready_for_history_limit,
    check_memory_added_to_chat_history,
    check_memory_ready_for_chat_history,
    check_organization_memory_enabled,
    check_passed_meta_question_gate,
    check_ready_for_stop,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
    check_user_memory_retrieval_enabled,
    check_user_memory_storage_enabled,
)
from swiss_ai_hub.agent.rag.step_functions import (
    do_condense_standalone_question,
    do_context_sufficient_guard,
    do_few_shot_guard,
    do_finalize_rag_stop,
    do_limit_chat_history,
    do_limit_chat_history_with_context,
    do_order_nodes_by_documents,
    do_rerank_nodes,
    do_respond_with_llm,
    do_retrieve,
)
from swiss_ai_hub.agent.self_awareness.self_awareness_mixin import SelfAwarenessMixin
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: RAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config is not None)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config is not None)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when InOrderNodeCombinerEvent is present AND ContextSufficientAcceptEvent is present.
    """
    return check_context_ready_for_history_limit(context_sufficient_event)


@precondition()
async def organization_memory_enabled(
    config: RAGAgentConfig,
    start_event: UserMessageEvent | RAGStartEvent,
    clear: NotAMetaQuestionEvent | None = None,
) -> bool:
    """Precondition to check if organization memory retrieval is enabled (gated by meta-question detection)."""
    return check_passed_meta_question_gate(start_event, clear) and check_organization_memory_enabled(config)


@precondition()
async def user_memory_retrieval_enabled(
    config: RAGAgentConfig,
    start_event: UserMessageEvent | RAGStartEvent,
    clear: NotAMetaQuestionEvent | None = None,
) -> bool:
    """Precondition to check if user memory retrieval is enabled (gated by meta-question detection)."""
    return check_passed_meta_question_gate(start_event, clear) and check_user_memory_retrieval_enabled(config)


@precondition()
async def user_memory_storage_enabled(config: RAGAgentConfig) -> bool:
    """Precondition to check if user memory storage is enabled."""
    return check_user_memory_storage_enabled(config)


@precondition()
async def memory_ready_for_chat_history(
    config: RAGAgentConfig,
    start_event: UserMessageEvent | RAGStartEvent,
    clear: NotAMetaQuestionEvent | None = None,
    user_memory_event: RetrieveUserMemoryEvent | None = None,
    org_memory_event: RetrieveOrganizationMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required memory events are present before extending chat history."""
    return check_passed_meta_question_gate(start_event, clear) and check_memory_ready_for_chat_history(
        config, user_memory_event, org_memory_event
    )


@precondition()
async def memory_added_to_chat_history(
    config: RAGAgentConfig,
    start_event: UserMessageEvent | RAGStartEvent,
    clear: NotAMetaQuestionEvent | None = None,
    memory_history_event: AddMemoryToChatHistoryEvent | None = None,
) -> bool:
    """Precondition to ensure memory has been added to chat history when required (gated by meta detection)."""
    return check_passed_meta_question_gate(start_event, clear) and check_memory_added_to_chat_history(
        config, memory_history_event
    )


@precondition()
async def ready_for_stop(
    config: RAGAgentConfig,
    store_memory_event: StoreUserMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required steps are complete before stopping."""
    return check_ready_for_stop(config, store_memory_event)


class RAGAgent(SelfAwarenessMixin, Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Retrieve user memories (personalized context) for individualized responses
    - Retrieve organization memories (expert knowledge) for shared context
    - Store new user memories from conversations for future retrieval
    - Limit chat history to fit input token limits
    - Condense chat history into standalone question
    - Retrieve relevant documents from a knowledge base
    - Order retrieved nodes for better contextual relevance
    - Generate responses using an LLM based on the context and retrieved information

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.description")
    icon: ClassVar[str] = "mage:file"

    def self_awareness_llm_config(self, agent_config: RAGAgentConfig) -> LLMConfig:
        return agent_config.llm

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def detect_meta_question_step(
        self,
        event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Gate every chat message: classify it as a meta question or release the normal RAG pipeline."""
        return await self.run_meta_question_detection(event.user_query, agent_config, displayer, t)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        self,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """Answer a meta question from the agent's own identity and workflow, then stop the run."""
        return await self.run_meta_question_answer(event, user_message_event.messages, agent_config, displayer, t)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_user_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_user_memory.description"),
        icon="mdi:account-circle",
        precondition=user_memory_retrieval_enabled,
    )
    async def retrieve_user_memory_step(
        self,
        event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        memory: AgentMemory,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> RetrieveUserMemoryEvent:
        """Retrieve user memories for personalized context."""
        query = event.user_query
        memory_result = await memory.search_user_memory(
            query=query,
            user_id=event.user.id,
            limit=10,
            threshold=0.5,
            rerank=agent_config.user_memory.rerank_user_memory,
        )

        return RetrieveUserMemoryEvent.from_memory_search_result(memory_result)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_organization_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_organization_memory.description"),
        icon="mdi:brain",
        precondition=organization_memory_enabled,
    )
    async def retrieve_organization_memory_step(
        self,
        event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        memory: AgentMemory,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> RetrieveOrganizationMemoryEvent:
        """Retrieve organization memories for expert knowledge context."""
        assert agent_config.org_memory is not None  # precondition enforces this
        org_memory = agent_config.org_memory
        query = event.user_query
        requested = event.org_memory_namespaces if isinstance(event, RAGStartEvent) else []
        tenant_namespaces = OrgMemoryNamespaceResolver.resolve_for_search(
            requested=requested,
            configured=org_memory.allowed_tenant_namespaces,
        )
        memory_result = await memory.search_organization_memory(
            query=query,
            tenant_id=org_memory.tenant_id,
            tenant_namespaces=tenant_namespaces,
            user_id=None,
            limit=10,
            threshold=0.5,
            rerank=org_memory.rerank_organization_memory,
        )

        return RetrieveOrganizationMemoryEvent.from_memory_search_result(memory_result)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.add_memory_to_context.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.add_memory_to_context.description"),
        icon="mdi:database-plus",
        precondition=memory_ready_for_chat_history,
    )
    async def add_memory_to_chat_history_step(
        self,
        user_message_event: UserMessageEvent | RAGStartEvent,
        user_memory_event: RetrieveUserMemoryEvent | None,
        org_memory_event: RetrieveOrganizationMemoryEvent | None,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> AddMemoryToChatHistoryEvent:
        """Extend chat history with memory context (user and/or organization)."""
        chat_history = user_message_event.messages

        # Add user memory first (more personal context)
        if agent_config.user_memory.enable_user_memory_retrieval and user_memory_event is not None:
            chat_history = extend_chat_history_with_user_memory(
                chat_history=chat_history,
                memories=user_memory_event.memories,
                relations=user_memory_event.relations,
                user=user_message_event.user,
                t=t,
            )

        # Add organization memory second (broader context)
        if agent_config.org_memory is not None and org_memory_event is not None:
            chat_history = extend_chat_history_with_organization_memory(
                chat_history=chat_history,
                memories=org_memory_event.memories,
                relations=org_memory_event.relations,
                t=t,
            )

        return AddMemoryToChatHistoryEvent(extended_history=chat_history)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
        precondition=memory_added_to_chat_history,
    )
    async def limit_chat_history_step(
        self,
        user_event: UserMessageEvent | RAGStartEvent,
        memory_history_event: AddMemoryToChatHistoryEvent | None,
        agent_config: RAGAgentConfig,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> LimitChatHistoryEvent:
        # Use extended history if memory was added, otherwise use original messages
        messages = memory_history_event.extended_history if memory_history_event is not None else user_event.messages
        return do_limit_chat_history(messages, agent_config.number_of_input_tokens)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.condense_standalone_question.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.condense_standalone_question.description"),
        icon="mage:archive",
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        return await do_condense_standalone_question(
            event.limited_history, start_event.last_user_message, agent_config.llm, displayer, t
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.description"),
        icon="mage:shield-check",
    )
    async def few_shot_guard_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            event.condensed_chat_message.content,
            agent_config.few_shot_guard_examples,
            agent_config.llm,
            displayer,
            t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_nodes.description"),
        icon="mage:search",
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        if isinstance(start_event, RAGStartEvent):
            runtime_configs = narrow_retrievers(
                agent_config.retrievers,
                start_event.selected_namespaces,
                start_event.additional_filters,
            )
        else:
            runtime_configs = [RetrievalRuntimeConfig.from_config(r) for r in agent_config.retrievers]
        return await do_retrieve(event, runtime_configs, t)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.rerank_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.rerank_nodes.description"),
        icon="mage:arrow-down",
        precondition=reranking_enabled,
    )
    async def rerank_nodes_step(
        self,
        event: RetrieverEvent,
        condense_event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RerankerEvent:
        return await do_rerank_nodes(
            event.nodes, condense_event.condensed_chat_message.content, agent_config.reranking_config, displayer, t
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.order_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.order_nodes.description"),
        icon="mage:arrowlist",
        precondition=reranking_complete_or_disabled,
    )
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent | RerankerEvent,
        t: LocaleHandler,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        return await do_order_nodes_by_documents(event, t, agent_config.context_prompt, displayer)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.context_sufficient_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.context_sufficient_guard.description"),
        icon="mage:check-circle",
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        guard_config: ContextSufficientGuardStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: InOrderNodeCombinerEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        chat_history_event: LimitChatHistoryEvent,
        run_context: RunContext,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        return await do_context_sufficient_guard(
            user_query_event.condensed_chat_message.content,
            event.context_message,
            guard_config.check_context_sufficiency,
            guard_config.max_hops,
            run_context,
            agent_config.llm,
            displayer,
            t,
            chat_history=chat_history_event.limited_history,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history_with_context.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.rag_agent.steps.limit_chat_history_with_context.description"
        ),
        icon="mage:edit",
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        return do_limit_chat_history_with_context(
            context_event.context_message,
            chat_history_event.limited_history,
            start_event.last_user_message,
            agent_config.llm.token_counter,
            agent_config.number_of_input_tokens,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        guard_config: ContextSufficientGuardStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        # Use as_stop_step=False to return LLMEvent (not LLMStopEvent)
        # This allows store_user_memory_step to run before the final stop_step
        return await do_respond_with_llm(
            event,
            limited_history_without_context.limited_history,
            guard_config.context_insufficient_prompt,
            agent_config.system_prompt,
            agent_config.llm,
            displayer,
            t,
            as_stop_step=False,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.store_user_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.store_user_memory.description"),
        icon="mdi:content-save",
        precondition=user_memory_storage_enabled,
    )
    async def store_user_memory_step(
        self,
        user_message_event: UserMessageEvent | RAGStartEvent,
        llm_event: LLMEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
    ) -> StoreUserMemoryEvent:
        """Store new user memories from the conversation."""
        memory_added = await memory.add_user_memory(
            messages=llm_event.chat_messages,
            user_id=user_message_event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        return StoreUserMemoryEvent.from_memory_added_object(memory_added)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.stop.description"),
        precondition=ready_for_stop,
    )
    async def stop_step(
        self,
        llm_event: LLMEvent,
        _store_memory_event: StoreUserMemoryEvent | None,
        few_shot_reject: FewShotRejectEvent | None,
        context_insufficient_reject: ContextInsufficientRejectEvent | None,
        agent_config: RAGAgentConfig,
    ) -> RAGSuccessStopEvent | RAGFailureStopEvent:
        """Final step that ensures all required steps are complete before stopping."""
        return do_finalize_rag_stop(
            llm_event=llm_event,
            expert_answer_context=None,
            few_shot_reject=few_shot_reject,
            context_insufficient_reject=context_insufficient_reject,
        )
