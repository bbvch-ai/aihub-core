import asyncio
import logging
from collections.abc import Callable

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    MemoryStorageRequestedEvent,
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGStartEvent,
    RAGSuccessStopEvent,
    RerankerEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    StandaloneQuestionCondenserEvent,
    StoreUserMemoryRequestedEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    AgentMemory,
    IngestedNode,
    LLMConfig,
    OrgMemoryNamespaceResolver,
    OrgMemoryReadConfig,
    RetrievalRuntimeConfig,
    combine_nodes_in_order,
    condense_standalone_question,
    context_sufficient_guard,
    few_shot_guard,
    limit_chat_history,
    limit_chat_history_with_context,
    merge_consecutive_messages,
    rerank_nodes,
    retrieve_from_all_sources,
)
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.memory_writer_agent.configs.memory_writer_agent_config import MemoryWriterAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.limit_chat_history_with_context_event import (
    LimitChatHistoryWithContextEvent,
)
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

logger = logging.getLogger(__name__)

PREV_GROUNDING_NODES_KEY = "prev_grounding_nodes"

# Bounds a hung backend, not normal latency: well above the ~0.25s graph-free median from issue #1713.
MEMORY_RETRIEVAL_TIMEOUT_SECONDS = 15.0


def do_limit_chat_history(
    messages: list[ChatMessage],
    number_of_input_tokens: int,
) -> LimitChatHistoryEvent:
    """Truncate chat messages to fit within token limit."""
    limited = limit_chat_history(chat_history=messages, number_of_input_tokens=number_of_input_tokens)
    return LimitChatHistoryEvent(limited_history=limited)


async def do_condense_standalone_question(
    limited_history: list[ChatMessage],
    last_user_message: ChatMessage,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity,
) -> StandaloneQuestionCondenserEvent:
    """Condense chat history and user query into standalone question."""
    await displayer.display_thought(t("agent.thought.condense_question"))
    async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
        condensed = await condense_standalone_question(
            chat_history=limited_history, message=last_user_message, t=t, llm=llm
        )
        return StandaloneQuestionCondenserEvent(condensed_chat_message=condensed)


async def do_respond_with_llm(
    event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent,
    limited_history_without_context: list[ChatMessage],
    context_insufficient_prompt: LocaleString | None,
    system_prompt: LocaleString | None,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity,
    as_stop_step: bool = True,
) -> LLMStopEvent | LLMEvent:
    """Generate LLM response with proper message building and streaming."""
    await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))

    if isinstance(event, FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent):
        context_insufficient_prompt_text = t.extract(context_insufficient_prompt)
        prompt_text = t("agent.prompt.guard.reject").format(
            prompt=context_insufficient_prompt_text, reason=event.reason
        )
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt_text,
            ),
        ] + limited_history_without_context
    else:
        messages = event.limited_history_with_context

    system_prompt_text = t.extract(system_prompt) if system_prompt else None
    if system_prompt_text:
        system_message = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt_text)
        messages = [system_message] + messages

    # Merge consecutive messages with the same role (required by LiteLLM)
    messages = merge_consecutive_messages(messages)

    async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
        return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=as_stop_step)


async def do_few_shot_guard(
    condensed_question: str | None,
    examples: list | None,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity,
) -> FewShotRejectEvent | FewShotAcceptEvent:
    """Execute few-shot guard logic and return appropriate event."""
    if not examples:
        return FewShotAcceptEvent(reason=t("agent.thought.no_few_shot_examples"))

    async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
        guard_result = await few_shot_guard(
            llm=llm,
            t=t,
            user_query=condensed_question,
            examples=examples,
        )

    if not guard_result.success:
        return FewShotRejectEvent(reason=guard_result.reasoning)

    return FewShotAcceptEvent(reason=guard_result.reasoning)


async def do_retrieve_user_memory(
    event: UserMessageEvent | RAGStartEvent,
    memory: AgentMemory,
    rerank: bool,
) -> RetrieveUserMemoryEvent:
    """Retrieve user memories for personalized context.

    A failing memory subsystem degrades to an empty event instead of propagating (issue #1713): raising
    would end the run, while `stop_on_error=False` would suppress the `ExceptionEvent` but emit nothing at
    all — and `check_memory_ready_for_chat_history` blocks until this event exists, so the run would hang.
    A hung backend degrades the same way, since a stall blocks the chat turn just as a raise ends it.
    """
    user_id = event.user.id
    try:
        memory_result = await asyncio.wait_for(
            memory.search_user_memory(
                query=event.user_query,
                user_id=user_id,
                limit=10,
                threshold=0.5,
                rerank=rerank,
            ),
            timeout=MEMORY_RETRIEVAL_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning(
            "User memory retrieval failed; answering without user memory. user_id=%s",
            user_id,
            exc_info=True,
        )
        return RetrieveUserMemoryEvent(memories=[], relations=[])

    return RetrieveUserMemoryEvent.from_memory_search_result(memory_result)


async def do_retrieve_organization_memory(
    event: UserMessageEvent | RAGStartEvent,
    org_memory: OrgMemoryReadConfig,
    memory: AgentMemory,
) -> RetrieveOrganizationMemoryEvent:
    """Retrieve organization memories for shared expert-knowledge context.

    Degrades to an empty event on failure for the same reason as `do_retrieve_user_memory`.

    Namespace resolution is deliberately left outside that safety net: a start event asking for a namespace
    outside the configured allow-list is a caller error, and silently answering from the wrong scope (or
    from none) would hide it. Only the memory-subsystem call degrades.
    """
    requested = event.org_memory_namespaces if isinstance(event, RAGStartEvent) else []
    tenant_namespaces = OrgMemoryNamespaceResolver.resolve_for_search(
        requested=requested,
        configured=org_memory.allowed_tenant_namespaces,
    )
    try:
        memory_result = await asyncio.wait_for(
            memory.search_organization_memory(
                query=event.user_query,
                tenant_id=org_memory.tenant_id,
                tenant_namespaces=tenant_namespaces,
                user_id=None,
                limit=10,
                threshold=0.5,
                rerank=org_memory.rerank_organization_memory,
            ),
            timeout=MEMORY_RETRIEVAL_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning(
            "Organization memory retrieval failed; answering without organization memory. "
            "tenant_id=%s namespaces=%s user_id=%s",
            org_memory.tenant_id,
            tenant_namespaces,
            # Organization memory is tenant-scoped and runs without an identity, so this log line is the one
            # place a delegated, identity-less run would still dereference the absent user — turning a
            # recoverable memory hiccup into the AttributeError that ends the run.
            event.user.id if event.user else None,
            exc_info=True,
        )
        return RetrieveOrganizationMemoryEvent(memories=[], relations=[])

    return RetrieveOrganizationMemoryEvent.from_memory_search_result(memory_result)


async def do_retrieve(
    event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
    runtime_configs: list[RetrievalRuntimeConfig],
    t: LocaleHandler,
    user: UserIdentity,
) -> RetrieverEvent:
    """Retrieve nodes from all sources and return RetrieverEvent."""
    if isinstance(event, StandaloneQuestionCondenserEvent):
        query = event.condensed_chat_message.content or ""
    else:
        query = event.new_query
    all_nodes = await retrieve_from_all_sources(query, runtime_configs, t, user)
    nodes_with_score = [node.to_llama_index_node_with_score() for node in all_nodes]
    return RetrieverEvent.from_nodes(nodes_with_score)


async def do_rerank_nodes(
    nodes: list[IngestedNode],
    query: str | None,
    reranking_config: RerankingConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity,
) -> RerankerEvent:
    """Rerank nodes and build RerankerEvent."""
    await displayer.display_thought(t("agent.thought.reranking_results"))
    reranked_nodes = await rerank_nodes(
        nodes=nodes,
        query=query,
        reranking_model=reranking_config.reranking_model,
        user=user,
    )

    return RerankerEvent(
        query=query,
        rerank_model_name=reranking_config.reranking_model.model_name,
        top_n=reranking_config.reranking_model.top_n,
        input_nodes=nodes,
        output_nodes=reranked_nodes,
        reranked=reranking_config.reranking_model is not None,
    )


async def do_order_nodes_by_documents(
    event: RetrieverEvent | RerankerEvent,
    t: LocaleHandler,
    context_prompt: LocaleString | None,
    displayer: EventDisplayer,
    carried_nodes: list[IngestedNode] | None = None,
) -> InOrderNodeCombinerEvent:
    """Order nodes and return InOrderNodeCombinerEvent.

    Carried nodes are prior-turn grounding documents (see `ThreadContext`); they are merged in as
    regular reference documents so a follow-up turn keeps the source that grounded the offer, even
    when the cold retrieval drops it.
    """
    await displayer.display_thought(t("agent.thought.searching_knowledge"))
    fresh_nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
    fresh_nodes = fresh_nodes or []
    fresh_ids = {node.id for node in fresh_nodes}
    carried_new = [node for node in (carried_nodes or []) if node.id not in fresh_ids]
    merged_nodes = fresh_nodes + carried_new
    context_message = combine_nodes_in_order(
        context_nodes=merged_nodes,
        t=t,
        context_prompt=context_prompt,
    )
    return InOrderNodeCombinerEvent(context_message=context_message, grounding_nodes=merged_nodes)


async def do_read_carried_grounding_nodes(thread_context: ThreadContext) -> list[IngestedNode]:
    """Read prior-turn grounding nodes persisted in the thread (empty list when none)."""
    raw_nodes = await thread_context.get(PREV_GROUNDING_NODES_KEY, [])
    return [IngestedNode.model_validate(node) for node in raw_nodes]


async def do_persist_grounding_nodes(
    thread_context: ThreadContext,
    nodes: list[IngestedNode],
    top_n: int = 2,
) -> None:
    """Persist the top-N grounding nodes of this turn for the next turn to carry forward (overwrites)."""
    await thread_context.set(
        PREV_GROUNDING_NODES_KEY,
        [node.model_dump(mode="json") for node in nodes[:top_n]],
    )


async def do_context_sufficient_guard(
    user_query: str | None,
    context_message: ChatMessage | None,
    check_context_sufficiency: bool | None,
    max_hops: int,
    run_context: RunContext,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    chat_history: list[ChatMessage],
    user: UserIdentity,
) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
    if not check_context_sufficiency:
        return ContextSufficientAcceptEvent(reason=t("agent.thought.no_context_sufficiency_check"))

    prev_queries = await run_context.get("prev_queries", [])
    hop_count = await run_context.get("hop_count", 1)
    more_hops_available = hop_count < max_hops

    async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
        guard_result = await context_sufficient_guard(
            llm=llm,
            t=t,
            user_query=user_query,
            context_message=context_message,
            prev_queries=prev_queries,
            more_hops_available=more_hops_available,
            chat_history=chat_history,
        )

    if guard_result.success:
        await displayer.display_thought(t("agent.thought.context_sufficient"))
        return ContextSufficientAcceptEvent(reason=guard_result.reasoning)

    if not more_hops_available:
        return ContextInsufficientRejectEvent(reason=guard_result.reasoning)

    await run_context.set("hop_count", hop_count + 1)
    new_query = guard_result.new_query
    prev_queries.append(new_query)
    await run_context.set("prev_queries", prev_queries)
    await displayer.display_thought(t("agent.thought.trying_another_retrieval_hop"))
    return ContextInsufficientWithQueryEvent(reason=guard_result.reasoning, new_query=new_query)


def do_limit_chat_history_with_context(
    context_message: ChatMessage,
    chat_history: list[ChatMessage],
    last_user_message: ChatMessage | None,
    tokenizer: Callable[[str], list[int]],
    number_of_input_tokens: int,
) -> LimitChatHistoryWithContextEvent:
    """Limit chat history including context and return event."""
    system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
    limited_history = limit_chat_history_with_context(
        chat_history=chat_history,
        context_messages=[context_message],
        system_messages=system_messages,
        last_user_message=last_user_message or ChatMessage(role=MessageRole.USER, content=""),
        tokenizer=tokenizer,
        number_of_input_tokens=number_of_input_tokens,
    )
    return LimitChatHistoryWithContextEvent(limited_history_with_context=limited_history)


def do_finalize_rag_stop(
    llm_event: LLMEvent,
    expert_answer_context: ExpertAnswerContextEvent | None,
    few_shot_reject: FewShotRejectEvent | None,
    context_insufficient_reject: ContextInsufficientRejectEvent | None,
) -> RAGSuccessStopEvent | RAGFailureStopEvent:
    """Resolve the final RAG stop event from the run's reject/accept signals."""
    answer = llm_event.output_messages[-1].content if llm_event.output_messages else None
    # Expert-supplied context grounds the answer and overrides any earlier "context insufficient" verdict.
    if expert_answer_context is not None:
        return RAGSuccessStopEvent(answer=answer)
    # Few-shot rejection is decided before retrieval, so its verdict wins over context-sufficiency outcomes.
    if few_shot_reject is not None:
        return RAGFailureStopEvent(reason=RAGFailureReason.FEW_SHOT_REJECTED, answer=answer)
    if context_insufficient_reject is not None:
        return RAGFailureStopEvent(reason=RAGFailureReason.CONTEXT_INSUFFICIENT, answer=answer)
    return RAGSuccessStopEvent(answer=answer)


def build_memory_storage_request(
    user: UserIdentity,
    messages: list[ChatMessage],
    topic: AgentInstanceTopic,
    agent_config: AgentConfig,
    locale: str,
) -> MemoryStorageRequestedEvent:
    """
    Build the detached memory-storage delegation targeting the `MemoryWriterAgent` (issue #1179).

    Carries the originating agent's identity (from the topic + config) so the writer rebuilds the *same*
    `AgentMemory` — preserving the fact-extraction prompt and the `_agent_id` scoping tag.
    """
    return MemoryStorageRequestedEvent(
        start_event=StoreUserMemoryRequestedEvent(
            user=user,
            messages=messages,
            locale=locale,
            origin_thread_id=topic.thread_id,
            origin_display_id=topic.display_id,
            origin_run_id=topic.run_id,
            origin_agent_class=topic.agent_class,
            origin_agent_id=agent_config.agent_id,
            origin_agent_name=agent_config.name,
            origin_agent_description=agent_config.description,
        ),
        # Routing target carried on the event (not hard-coded in the dispatcher by design) so the delegation
        # primitive stays generic; today it resolves to the single MemoryWriterAgent system instance.
        target_agent_class=MemoryWriterAgentConfig.AGENT_CLASS,
        target_agent_id=MemoryWriterAgentConfig.AGENT_ID,
    )
