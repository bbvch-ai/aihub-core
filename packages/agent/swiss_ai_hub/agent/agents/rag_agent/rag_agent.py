from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ConversationQueryEvent,
    EnrichedChatHistoryEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    RAGFailureStopEvent,
    RAGStartEvent,
    RAGSuccessStopEvent,
    RerankerEvent,
    RetrieverEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import RetrievalRuntimeConfig, narrow_retrievers
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.limit_chat_history_with_context_event import (
    LimitChatHistoryWithContextEvent,
)
from swiss_ai_hub.agent.capabilities.conversation.conversation_capability import ConversationCapability
from swiss_ai_hub.agent.capabilities.conversation.conversation_preconditions import all_post_answer_hooks_reported
from swiss_ai_hub.agent.capabilities.memory.memory_capability import MemoryCapability
from swiss_ai_hub.agent.capabilities.self_awareness.self_awareness_capability import SelfAwarenessCapability
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import generate_follow_up_questions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.rag.preconditions import check_reranking_complete_or_disabled, check_reranking_enabled
from swiss_ai_hub.agent.rag.step_functions import (
    do_context_sufficient_guard,
    do_few_shot_guard,
    do_finalize_rag_stop,
    do_limit_chat_history,
    do_limit_chat_history_with_context,
    do_order_nodes_by_documents,
    do_persist_grounding_nodes,
    do_read_carried_grounding_nodes,
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
async def reranking_enabled(event: RetrieverEvent, config: RAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config is not None)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config is not None)


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The blueprint itself is retrieval: it takes the enriched conversation, guards it, retrieves and orders
    grounding documents, and answers from them. Everything a chat agent shares — the meta-question gate,
    the turn's query, memory, the context join, the title and follow-ups — comes from the installed
    capabilities, and the RAG-specific stop event is why the blueprint keeps its own stop step.

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.description")
    icon: ClassVar[str] = "mage:file"

    capabilities = (ConversationCapability, SelfAwarenessCapability, MemoryCapability)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        user_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent | RAGFailureStopEvent:
        """The entry step: both start events become the limited history the spine picks up from.

        Not gated on meta-question detection: limiting is cheap and side-effect free, and the spine holds
        everything after it. A programmatic start hands its organization-memory scope to the memory
        capability through the run context, since the capability cannot name this blueprint's start event.
        """
        if isinstance(user_event, RAGStartEvent):
            await run_context.set(MemoryCapability.REQUESTED_ORG_NAMESPACES_KEY, user_event.org_memory_namespaces)
        return await do_limit_chat_history(
            user_event.messages,
            agent_config.number_of_input_tokens,
            user_event.last_user_message,
            [agent_config.llm, agent_config.task_llm],
            displayer,
            t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.description"),
        icon="mage:shield-check",
    )
    async def few_shot_guard_step(
        self,
        event: ConversationQueryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            event.query,
            agent_config.few_shot_guard_examples,
            agent_config.task_llm,
            displayer,
            t,
            user,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.retrieve_nodes.description"),
        icon="mage:search",
    )
    async def retrieve_step(
        self,
        event: ConversationQueryEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        user: UserIdentity | None = None,
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
        return await do_retrieve(event, runtime_configs, t, user)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.rerank_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.rerank_nodes.description"),
        icon="mage:arrow-down",
        precondition=reranking_enabled,
    )
    async def rerank_nodes_step(
        self,
        event: RetrieverEvent,
        query: ConversationQueryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> RerankerEvent:
        return await do_rerank_nodes(
            event.nodes,
            query.query,
            agent_config.reranking_config,
            displayer,
            t,
            user,
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
        thread_context: ThreadContext,
    ) -> InOrderNodeCombinerEvent:
        carried_nodes = await do_read_carried_grounding_nodes(thread_context)
        return await do_order_nodes_by_documents(
            event, t, agent_config.context_prompt, displayer, carried_nodes=carried_nodes
        )

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
        query: ConversationQueryEvent,
        history: EnrichedChatHistoryEvent,
        run_context: RunContext,
        user: UserIdentity | None = None,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        return await do_context_sufficient_guard(
            query.query,
            event.context_message,
            guard_config.check_context_sufficiency,
            guard_config.max_hops,
            run_context,
            agent_config.task_llm,
            displayer,
            t,
            chat_history=history.extended_history,
            user=user,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.persist_grounding_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.persist_grounding_nodes.description"),
        icon="mdi:content-save-cog",
    )
    async def persist_grounding_nodes_step(
        self,
        _: ContextSufficientAcceptEvent,
        event: RerankerEvent | RetrieverEvent,
        thread_context: ThreadContext,
    ) -> None:
        """Persist this turn's top grounding nodes so a follow-up turn can carry them forward.

        Gated on acceptance so we never persist context the guard judged insufficient. On a multi-hop
        run the dispatcher injects the latest (approved) RerankerEvent/RetrieverEvent.
        """
        nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
        await do_persist_grounding_nodes(thread_context, nodes or [])

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.limit_chat_history_with_context.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.rag_agent.steps.limit_chat_history_with_context.description"
        ),
        icon="mage:edit",
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: InOrderNodeCombinerEvent,
        history: EnrichedChatHistoryEvent,
        _: ContextSufficientAcceptEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        return do_limit_chat_history_with_context(
            context_event.context_message,
            history.extended_history,
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
        history: EnrichedChatHistoryEvent,
        agent_config: RAGAgentConfig,
        guard_config: ContextSufficientGuardStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> LLMEvent:
        """Answer as a non-terminal `LLMEvent` so the post-answer hooks run before the stop step."""
        return await do_respond_with_llm(
            event,
            history.extended_history,
            guard_config.context_insufficient_prompt,
            agent_config.system_prompt,
            agent_config.llm,
            displayer,
            t,
            user,
            as_stop_step=False,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.stop.description"),
        precondition=all_post_answer_hooks_reported,
    )
    async def stop_step(
        self,
        llm_event: LLMEvent,
        few_shot_reject: FewShotRejectEvent | None,
        context_insufficient_reject: ContextInsufficientRejectEvent | None,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        _hooks: list[AnswerPostProcessedEvent] | None = None,
    ) -> RAGSuccessStopEvent | RAGFailureStopEvent:
        """The blueprint's own stop, kept because its stop event tells a caller how the run ended.

        Waits on the spine's post-answer barrier like the default stop would, and generates the follow-up
        questions inline for the same reason: they are grounded on the answer and must be on the wire
        before teardown.
        """
        await generate_follow_up_questions(
            chat_messages=llm_event.chat_messages,
            llm_config=agent_config.task_llm,
            displayer=displayer,
            user=user,
            t=t,
        )
        return do_finalize_rag_stop(
            llm_event=llm_event,
            expert_answer_context=None,
            few_shot_reject=few_shot_reject,
            context_insufficient_reject=context_insufficient_reject,
        )
