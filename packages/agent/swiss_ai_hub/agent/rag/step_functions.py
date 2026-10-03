import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ConversationContextualizedEvent,
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGSuccessStopEvent,
    RefusalReason,
    RefusalStopEvent,
    RerankerEvent,
    RetrieverEvent,
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.generative_ai import (
    IngestedNode,
    LLMConfig,
    RetrievalRuntimeConfig,
    combine_nodes_in_order,
    context_sufficient_guard,
    estimate_prompt_tokens,
    few_shot_guard,
    limit_chat_history,
    rerank_nodes,
    retrieve_from_all_sources,
    usable_input_budget,
)
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

logger = logging.getLogger(__name__)

PREV_GROUNDING_NODES_KEY = "prev_grounding_nodes"


def effective_input_token_limit(
    number_of_input_tokens: int,
    llm_configs: list[LLMConfig | None],
) -> int:
    """The admin's cost ceiling capped by the narrowest model window that could receive the prompt.

    `number_of_input_tokens` is a cost ceiling and may sit above the model's real context window, so
    trimming to it alone does not bound what the provider will accept. Falls back to the ceiling when no
    window can be established, matching `usable_input_budget`'s fail-open contract.
    """
    budget = usable_input_budget(llm_configs)
    return number_of_input_tokens if budget is None else min(number_of_input_tokens, budget)


async def do_limit_chat_history(
    messages: list[ChatMessage],
    number_of_input_tokens: int,
    last_user_message: ChatMessage,
    llm_configs: list[LLMConfig | None],
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> LimitChatHistoryEvent | RefusalStopEvent:
    """Truncate chat messages to the configured token limit, and refuse the run if the result still cannot be sent.

    Truncation alone cannot bound the prompt. `ChatMemoryBuffer.get` falls through to `chat_history[-1:]` when even
    one message exceeds the limit (llama-index-core 0.14.22) -- deliberately, so the model reports the overflow
    rather than the history silently losing the question -- and `number_of_input_tokens` is an admin's cost ceiling,
    which may sit above the model's actual context window. A chat client that pastes a whole document into one turn
    therefore reaches the model regardless, and comes back as a provider 400 wrapped in the gateway's fallback
    bookkeeping. Re-check that branch on a llama-index upgrade: a version returning `[]` instead would drop the
    user's question rather than keep it.

    Only the last turn is irreducible, and it is what decides: everything older is negotiable, so the history is
    trimmed against the model's window rather than the admin's ceiling, and the run is refused only when the turn
    alone already exceeds the window. That threshold is deliberately the impossible case rather than a prediction of
    any one step's prompt. `condense_standalone_question` really does pay for the turn twice -- it renders the
    limited history into its system prompt and appends the message again -- but tiktoken is not the served model's
    tokenizer and over-counts enough on non-Latin scripts that budgeting for the doubling refuses prompts the model
    accepts (121k tiktoken tokens of Vietnamese fit gemma-4-31B-it's 100k window on Infomaniak). A prompt that fits
    here and still overflows downstream gets the provider's own 400, which `ModelGatewayErrorHandler` rewrites into a
    sentence naming the limit.

    Refusing loses the thread's title, which `generate_conversation_title_step` anchors on the event this no longer
    emits. Generating one here would hand the same oversized turn to the same model and fail the same way.
    """
    budget = usable_input_budget(llm_configs)
    if budget is None:
        return LimitChatHistoryEvent(
            limited_history=limit_chat_history(chat_history=messages, number_of_input_tokens=number_of_input_tokens)
        )

    answering_config = next(config for config in llm_configs if config is not None)
    last_turn_tokens = estimate_prompt_tokens([last_user_message], answering_config.token_counter)
    if last_turn_tokens > budget:
        return await _refuse_oversized_input(last_turn_tokens, budget, answering_config.model_name, displayer, t)

    # Trim only what precedes the last turn, then put it back -- the same shape `Conversation.compose` uses for
    # the turns. Reserving room for the turn and then handing the trimmer a list that still contains it charges the
    # turn twice: no subset holding it fits the reduced limit, so `ChatMemoryBuffer` falls through to its most-recent-
    # message branch and the whole earlier conversation is dropped for any turn past half the budget.
    older_limit = min(number_of_input_tokens, budget - last_turn_tokens)
    limited = [*limit_chat_history(chat_history=messages[:-1], number_of_input_tokens=older_limit), *messages[-1:]]
    return LimitChatHistoryEvent(limited_history=limited)


async def _refuse_oversized_input(
    needed: int,
    budget: int,
    model_name: str,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> RefusalStopEvent:
    """Stop the run with a message the user can act on, keeping the token arithmetic to the thought.

    The chunk is what the chat renders; `output_messages` carries the same text for non-streaming consumers.
    """
    await displayer.display_thought(t("agent.conversation.thoughts.input_too_large", tokens=needed, budget=budget))
    refusal = t("agent.conversation.messages.input_too_large")
    await displayer.display_chunk(refusal, model_name=model_name)
    return RefusalStopEvent(
        reason=RefusalReason.INPUT_TOO_LARGE,
        output_messages=[Message.from_string(role="assistant", content=refusal, name=model_name)],
        chat_model_name=model_name,
    )


def do_answer_instructions(
    outcome: FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent | None,
    context_insufficient_prompt: LocaleString | None,
    system_prompt: LocaleString | None,
    t: LocaleHandler,
    cite_sources: bool = True,
) -> list[ChatMessage]:
    """The system messages the answer is written under: the profile's prompt, the citation rule, and on a
    rejection the reason the answer cannot come from the documents.

    With `cite_sources` the model is told to cite documents by their `id` attribute; chat clients turn those
    markers into their own source references.
    """
    system_prompt_text = t.extract(system_prompt) if system_prompt else None
    instructions = [
        text for text in (system_prompt_text, t("lib.prompt.citations.instruction") if cite_sources else None) if text
    ]
    messages = [ChatMessage(role=MessageRole.SYSTEM, content="\n\n".join(instructions))] if instructions else []
    if outcome is not None:
        reject_prompt = t("agent.prompt.guard.reject").format(
            prompt=t.extract(context_insufficient_prompt), reason=outcome.reason
        )
        messages.append(ChatMessage(role=MessageRole.SYSTEM, content=reject_prompt))
    return messages


def do_context_block(context_message: ChatMessage) -> list[ChatMessage]:
    """Retrieved or expert context as a block of the system head. A profile's context prompt may render it as a
    user message, which would otherwise land ahead of the conversation as a turn of its own."""
    return [ChatMessage(role=MessageRole.SYSTEM, blocks=context_message.blocks)]


async def do_respond_with_llm(
    messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity | None,
    as_stop_step: bool = True,
) -> LLMStopEvent | LLMEvent:
    """Stream the answer to the composed prompt, exactly as the composed-context event shows it."""
    await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))
    async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
        return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=as_stop_step)


async def do_few_shot_guard(
    condensed_question: str | None,
    examples: list | None,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    user: UserIdentity | None,
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


async def do_retrieve(
    event: ConversationContextualizedEvent | StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
    runtime_configs: list[RetrievalRuntimeConfig],
    t: LocaleHandler,
    user: UserIdentity | None,
) -> RetrieverEvent:
    """Retrieve nodes from all sources and return RetrieverEvent."""
    if isinstance(event, ConversationContextualizedEvent):
        query = event.query
    elif isinstance(event, StandaloneQuestionCondenserEvent):
        query = event.condensed_question
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
    user: UserIdentity | None,
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
    user: UserIdentity | None,
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
