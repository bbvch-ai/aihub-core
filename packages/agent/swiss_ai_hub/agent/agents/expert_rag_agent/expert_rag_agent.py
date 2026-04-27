from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AddMemoryToChatHistoryEvent,
    AgentInTheLoop,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    HumanInTheLoop,
    LimitChatHistoryEvent,
    LLMEvent,
    RAGStartEvent,
    RAGStopEvent,
    RerankerEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    StandaloneQuestionCondenserEvent,
    StopEvent,
    StoreUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    AgentMemory,
    RetrievalRuntimeConfig,
    extend_chat_history_with_organization_memory,
    extend_chat_history_with_user_memory,
    format_expert_conversation,
    narrow_retrievers,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.ask_expert_start_event import AskExpertStartEvent
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.limit_chat_history_with_context_event import (
    LimitChatHistoryWithContextEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.user_requests_expert_event import UserRequestsExpertEvent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.rag.preconditions import (
    check_context_ready_for_history_limit_with_expert,
    check_is_answer_response,
    check_is_no_answer_response,
    check_memory_added_to_chat_history,
    check_memory_ready_for_chat_history,
    check_organization_memory_enabled,
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
    do_limit_chat_history,
    do_limit_chat_history_with_context,
    do_order_nodes_by_documents,
    do_rerank_nodes,
    do_respond_with_llm,
    do_retrieve,
)
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config.enabled)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config.enabled)


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
    return check_context_ready_for_history_limit_with_expert(context_event, context_sufficient_event)


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer."""
    return check_is_answer_response(event)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful answer."""
    return check_is_no_answer_response(event)


@precondition()
async def organization_memory_enabled(config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if organization memory retrieval is enabled."""
    return check_organization_memory_enabled(config)


@precondition()
async def user_memory_retrieval_enabled(config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if user memory retrieval is enabled."""
    return check_user_memory_retrieval_enabled(config)


@precondition()
async def user_memory_storage_enabled(config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if user memory storage is enabled."""
    return check_user_memory_storage_enabled(config)


@precondition()
async def memory_ready_for_chat_history(
    config: ExpertRAGAgentConfig,
    user_memory_event: RetrieveUserMemoryEvent | None = None,
    org_memory_event: RetrieveOrganizationMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required memory events are present before extending chat history."""
    return check_memory_ready_for_chat_history(config, user_memory_event, org_memory_event)


@precondition()
async def memory_added_to_chat_history(
    config: ExpertRAGAgentConfig,
    memory_history_event: AddMemoryToChatHistoryEvent | None = None,
) -> bool:
    """Precondition to ensure memory has been added to chat history when required."""
    return check_memory_added_to_chat_history(config, memory_history_event)


@precondition()
async def ready_for_stop(
    config: ExpertRAGAgentConfig,
    store_memory_event: StoreUserMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required steps are complete before stopping."""
    return check_ready_for_stop(config, store_memory_event)


class ExpertRAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent with expert escalation.

    The ExpertRAGAgent extends the basic RAG functionality with the ability to consult
    human experts when the retrieved context is insufficient to answer the user's question.

    ### Features
    - Retrieve user memories (personalized context) for individualized responses
    - Retrieve organization memories (expert knowledge) for shared context
    - Store new user memories from conversations for future retrieval
    - Limit chat history to fit input token limits
    - Condense chat history into standalone question
    - Retrieve relevant documents from a knowledge base
    - Order retrieved nodes for better contextual relevance
    - Generate responses using an LLM based on the context and retrieved information
    - Expert escalation when context is insufficient (requires user consent)

    Note: For basic RAG functionality without expert escalation, use RAGAgent instead.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.expert_rag_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.expert_rag_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:building-a"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_user_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_user_memory.description"),
        icon="mdi:account-circle",
        precondition=user_memory_retrieval_enabled,
    )
    async def retrieve_user_memory_step(
        self,
        event: UserMessageEvent | RAGStartEvent,
        memory: AgentMemory,
    ) -> RetrieveUserMemoryEvent:
        """Retrieve user memories for personalized context."""
        query = event.user_query
        memory_result = await memory.search_user_memory(
            query=query,
            user_id=event.user.id,
            limit=10,
            threshold=0.5,
            rerank=True,
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
        agent_config: ExpertRAGAgentConfig,
        memory: AgentMemory,
    ) -> RetrieveOrganizationMemoryEvent:
        """Retrieve organization memories for expert knowledge context."""
        query = event.user_query
        memory_result = await memory.search_organization_memory(
            query=query,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
            user_id=None,
            limit=10,
            threshold=0.5,
            rerank=True,
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
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
    ) -> AddMemoryToChatHistoryEvent:
        """Extend chat history with memory context (user and/or organization)."""
        chat_history = user_message_event.messages

        # Add user memory first (more personal context)
        if agent_config.enable_user_memory_retrieval and user_memory_event is not None:
            chat_history = extend_chat_history_with_user_memory(
                chat_history=chat_history,
                memories=user_memory_event.memories,
                relations=user_memory_event.relations,
                user=user_message_event.user,
                t=t,
            )

        # Add organization memory second (broader context)
        if agent_config.enable_organization_memory and org_memory_event is not None:
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            event.condensed_chat_message.content, agent_config.few_shot_guard_examples, agent_config.llm, displayer, t
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
            event.context_message.content,
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
        context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: ExpertRAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        return do_limit_chat_history_with_context(
            context_event.context_message,
            chat_history_event.limited_history,
            start_event.last_user_message,
            agent_config.llm.token_counter,
            agent_config.number_of_input_tokens,
        )

    # --- Expert Escalation Steps ---

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.handle_insufficient_context.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.expert_rag_agent.steps.handle_insufficient_context.description"
        ),
        icon="mage:message-check",
    )
    async def insufficient_context_ask_expert_step(
        self,
        _: ContextInsufficientRejectEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.confirmation.request:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.context_not_sufficient"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.asking_for_consent"))
        return HumanInTheLoop.confirmation.invoke(question=t("agent.expert_rag_agent.messages.consent_question"))

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.consent_answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.consent_answer.description"),
        icon="mage:message-question-mark",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.confirmation.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserRequestsExpertEvent | ExpertRejectEvent:
        if event.response is True:
            await displayer.display_thought(t("agent.expert_rag_agent.thoughts.user_consented"))
            return UserRequestsExpertEvent()
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.user_declined"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.waiting_for_instructions"))
        return ExpertRejectEvent(reason="User declined expert escalation")

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.invoke_expert_agent.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.invoke_expert_agent.description"),
        icon="mage:robot",
    )
    async def forward_to_expert_asking_agent_step(
        self,
        user_message_event: UserMessageEvent | RAGStartEvent,
        _: UserRequestsExpertEvent,
        displayer: EventDisplayer,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_forwarding_confirmation"),
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            "\n",
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_answer_coming_soon"),
            model_name=ExpertRAGAgent.__name__,
        )
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_escalation.agent.agent_class,
            agent_id=agent_config.expert_escalation.agent.agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.user_query,
                locale=user_message_event.locale,
                user=user_message_event.user,
            ),
        )

    @step(
        precondition=is_answer_response,
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_positive.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_positive.description"),
        icon="mage:user-check",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> ExpertAnswerContextEvent:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.can_answer_question"))

        # Format the expert conversation as context
        expert_conversation = event.stop_event.expert_conversation
        expert_conversation_text = format_expert_conversation(expert_conversation)

        context_content = t("agent.prompt.expert_context", expert_conversation=expert_conversation_text)
        await displayer.display_thought(f"Expert context: {context_content}")

        context_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=context_content,
        )
        return ExpertAnswerContextEvent(context_message=context_message)

    @step(
        precondition=is_no_answer_response,
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_negative.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_negative.description"),
        icon="mage:user-cross",
    )
    async def expert_not_answered_step(
        self,
        displayer: EventDisplayer,
        _: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.expert_unable_to_answer"))
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_unable_to_answer"),
            model_name=ExpertRAGAgent.__name__,
        )
        return StopEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_error.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_error.description"),
        icon="mage:exclamation-circle",
    )
    async def expert_exception_step(
        self,
        displayer: EventDisplayer,
        exception_event: AgentInTheLoop.exception,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(
            t(
                "agent.expert_rag_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_error_occurred"),
            model_name=ExpertRAGAgent.__name__,
        )
        return StopEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ExpertRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: ExpertRAGAgentConfig,
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
        _llm_event: LLMEvent,
        _store_memory_event: StoreUserMemoryEvent | None,
        agent_config: ExpertRAGAgentConfig,
        run_context: RunContext,
    ) -> StopEvent:
        """Final step that ensures all required steps are complete before stopping."""
        context_sufficient = await run_context.get("context_sufficient", True)
        return RAGStopEvent(context_sufficient=context_sufficient)
