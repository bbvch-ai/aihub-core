from typing import ClassVar

from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    MemoryStorageRequestedEvent,
    RAGFailureStopEvent,
    RAGStartEvent,
    RAGSuccessStopEvent,
    RefusalStopEvent,
    RerankerEvent,
    RetrieverEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import RetrievalRuntimeConfig, UserScopedRetrievers, narrow_retrievers
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.rag.answer_hand_back import AnswerHandBack
from swiss_ai_hub.agent.rag.answer_prompt import AnswerPrompt
from swiss_ai_hub.agent.rag.citation_policy import CitationPolicy
from swiss_ai_hub.agent.rag.inaccessible_knowledge import InaccessibleKnowledge
from swiss_ai_hub.agent.rag.preconditions import check_reranking_complete_or_disabled, check_reranking_enabled
from swiss_ai_hub.agent.rag.step_functions import (
    do_context_block,
    do_context_sufficient_guard,
    do_few_shot_guard,
    do_finalize_rag_stop,
    do_limit_chat_history,
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

    The blueprint is retrieval: it guards the query, retrieves and orders grounding documents, and answers
    from them. It hands the conversation to the conversation capability (meta-question gate, query, title,
    follow-ups, stop), asks the memory capability for what it remembers, and asks for the prompt with those
    memories merged in. The outcome events are its own, passed to the completion as the stop.

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.rag_agent.metadata.description")
    icon: ClassVar[str] = "mage:file"
    completion_stops: ClassVar[tuple[type[StopEvent], ...]] = (RAGSuccessStopEvent, RAGFailureStopEvent)

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
    ) -> Conversation.ContextualizeRequest | RefusalStopEvent:
        """The entry step: both start events become the limited history the conversation picks up from.

        A programmatic start carries no user message, so the conversation skips meta-question inspection.
        """
        limited = await do_limit_chat_history(
            user_event.messages,
            agent_config.number_of_input_tokens,
            user_event.last_user_message,
            [agent_config.llm, agent_config.task_llm],
            displayer,
            t,
        )
        if isinstance(limited, RefusalStopEvent):
            return limited
        message = user_event if isinstance(user_event, UserMessageEvent) else None
        return Conversation.contextualize(history=limited.limited_history, message=message)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.gather_context.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.gather_context.description"),
        icon="mdi:brain",
    )
    async def gather_context_step(
        self,
        ctx: Conversation.Contextualized,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
    ) -> list[Memory.RecallRequest | AttachedFiles.ReadRequest | Knowledge.SearchRequest]:
        """A programmatic start may narrow the organization-memory scope; a chat message reads the profile's and may
        reference collections to search on top of the configured ones."""
        namespaces = start_event.org_memory_namespaces if isinstance(start_event, RAGStartEvent) else []
        references = start_event.knowledge_references if isinstance(start_event, UserMessageEvent) else []
        cite_sources = CitationPolicy.cites_sources(start_event)
        reserve = agent_config.retrieved_context_reserve() + agent_config.context_sufficient_guard_reserve(t, ctx.query)
        if references:
            reserve += agent_config.knowledge.context_reserve()
        files = AttachedFiles.read(
            start_event.files, ctx.history, ctx.query, reserve_tokens=reserve, cite_sources=cite_sources
        )
        return [Memory.recall(ctx.query, namespaces), files, Knowledge.search(references, ctx.query, cite_sources)]

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.few_shot_guard.description"),
        icon="mage:shield-check",
    )
    async def few_shot_guard_step(
        self,
        ctx: Conversation.Contextualized,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            ctx.query,
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
        event: Conversation.Contextualized | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        access: AccessChecker | None = None,
    ) -> RetrieverEvent | Conversation.CompleteRequest:
        """Retrieves relevant nodes from multiple knowledge sources in parallel, from what the asking user may read
        when the profile restricts retrieval to it. A run without a user keeps the profile's scope."""
        if isinstance(start_event, RAGStartEvent):
            runtime_configs = narrow_retrievers(
                agent_config.retrievers,
                start_event.selected_namespaces,
                start_event.additional_filters,
            )
        else:
            runtime_configs = [RetrievalRuntimeConfig.from_config(r) for r in agent_config.retrievers]
        if agent_config.restrict_to_user_access and access is not None and runtime_configs:
            runtime_configs = await UserScopedRetrievers.narrow(runtime_configs, access)
            if not runtime_configs:
                return await InaccessibleKnowledge.answer(agent_config.llm.model_name, displayer, t)
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
        ctx: Conversation.Contextualized,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> RerankerEvent:
        return await do_rerank_nodes(
            event.nodes,
            ctx.query,
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
        ctx: Conversation.Contextualized,
        memories: Memory.Recalled,
        files: AttachedFiles.Contents,
        knowledge: Knowledge.Searched,
        run_context: RunContext,
        user: UserIdentity | None = None,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        """The verdict weighs the retrieved documents against everything else the answer will see: a recalled
        memory, an attached file or a referenced collection may already answer the question."""
        return await do_context_sufficient_guard(
            ctx.query,
            event.context_message,
            guard_config.check_context_sufficiency,
            guard_config.max_hops,
            run_context,
            agent_config.task_llm,
            displayer,
            t,
            history=ctx.history,
            blocks=[*memories.blocks, knowledge.block, files.block],
            conversation=agent_config,
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
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.description"),
        icon="mdi:database-plus",
    )
    async def assemble_prompt_step(
        self,
        outcome: ContextSufficientAcceptEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        ctx: Conversation.Contextualized,
        memories: Memory.Recalled,
        files: AttachedFiles.Contents,
        knowledge: Knowledge.Searched,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: RAGAgentConfig,
        guard_config: ContextSufficientGuardStepConfig,
        t: LocaleHandler,
        documents: InOrderNodeCombinerEvent | None = None,
    ) -> Conversation.ComposeRequest:
        """One prompt per outcome, so the composed context is exactly what the model answers from: the retrieved
        documents when the guard accepted them, the reason it cannot answer from them otherwise."""
        accepted = isinstance(outcome, ContextSufficientAcceptEvent)
        return AnswerPrompt.compose(
            None if accepted else outcome,
            do_context_block(documents.context_message) if accepted and documents else [],
            ctx,
            (memories, files, knowledge),
            start_event,
            agent_config.system_prompt,
            guard_config.context_insufficient_prompt,
            t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(
        self,
        outcome: ContextSufficientAcceptEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        composed: Conversation.Composed,
        ctx: Conversation.Contextualized,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """Answer from the composed prompt, then hand the turn back with its outcome."""
        answer = await do_respond_with_llm(composed.history, agent_config.llm, displayer, t, user, as_stop_step=False)
        stop = do_finalize_rag_stop(
            llm_event=answer,
            expert_answer_context=None,
            few_shot_reject=outcome if isinstance(outcome, FewShotRejectEvent) else None,
            context_insufficient_reject=outcome if isinstance(outcome, ContextInsufficientRejectEvent) else None,
        )
        return AnswerHandBack.of(ctx, answer, stop, agent_config, topic, t, user)
