from collections.abc import Callable

from llama_index.core.base.llms.types import ChatMessage, MessageRole
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
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGSuccessStopEvent,
    RerankerEvent,
    RetrieverEvent,
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.generative_ai import (
    IngestedNode,
    LLMConfig,
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
) -> StandaloneQuestionCondenserEvent:
    """Condense chat history and user query into standalone question."""
    await displayer.display_thought(t("agent.thought.condense_question"))
    async with llm_config.cost_reporting_llm(displayer) as llm:
        condensed = condense_standalone_question(chat_history=limited_history, message=last_user_message, t=t, llm=llm)
        return StandaloneQuestionCondenserEvent(condensed_chat_message=condensed)


async def do_respond_with_llm(
    event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent,
    limited_history_without_context: list[ChatMessage],
    context_insufficient_prompt: LocaleString | None,
    system_prompt: LocaleString | None,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    as_stop_step: bool = True,
) -> LLMStopEvent | LLMEvent:
    """Generate LLM response with proper message building and streaming."""
    await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))

    if isinstance(event, FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent):
        context_insufficient_prompt_text = t.extract(context_insufficient_prompt)
        prompt_text = t("agent.prompt.guard.reject").format(
            prompt=context_insufficient_prompt_text, reason=event.reason
        )
        messages = limited_history_without_context + [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt_text,
            ),
        ]
    else:
        messages = event.limited_history_with_context

    system_prompt_text = t.extract(system_prompt) if system_prompt else None
    if system_prompt_text:
        system_message = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt_text)
        messages = [system_message] + messages

    # Merge consecutive messages with the same role (required by LiteLLM)
    messages = merge_consecutive_messages(messages)

    async with llm_config.cost_reporting_llm(displayer) as llm:
        return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=as_stop_step)


async def do_few_shot_guard(
    condensed_question: str | None,
    examples: list | None,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> FewShotRejectEvent | FewShotAcceptEvent:
    """Execute few-shot guard logic and return appropriate event."""
    if not examples:
        return FewShotAcceptEvent(reason=t("agent.thought.no_few_shot_examples"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
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
    event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
    runtime_configs: list[RetrievalRuntimeConfig],
    t: LocaleHandler,
) -> RetrieverEvent:
    """Retrieve nodes from all sources and return RetrieverEvent."""
    if isinstance(event, StandaloneQuestionCondenserEvent):
        query = event.condensed_chat_message.content or ""
    else:
        query = event.new_query
    all_nodes = await retrieve_from_all_sources(query, runtime_configs, t)
    nodes_with_score = [node.to_llama_index_node_with_score() for node in all_nodes]
    return RetrieverEvent.from_nodes(nodes_with_score)


async def do_rerank_nodes(
    nodes: list[IngestedNode],
    query: str | None,
    reranking_config: RerankingConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> RerankerEvent:
    """Rerank nodes and build RerankerEvent."""
    await displayer.display_thought(t("agent.thought.reranking_results"))
    reranked_nodes = await rerank_nodes(
        nodes=nodes,
        query=query,
        reranking_model=reranking_config.reranking_model,
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
) -> InOrderNodeCombinerEvent:
    """Order nodes and return InOrderNodeCombinerEvent."""
    await displayer.display_thought(t("agent.thought.searching_knowledge"))
    nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
    context_message = combine_nodes_in_order(
        context_nodes=nodes,
        t=t,
        context_prompt=context_prompt,
    )
    return InOrderNodeCombinerEvent(context_message=context_message)


async def do_context_sufficient_guard(
    user_query: str | None,
    context: str | None,
    check_context_sufficiency: bool | None,
    max_hops: int,
    run_context: RunContext,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    chat_history: list[ChatMessage],
) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
    if not check_context_sufficiency:
        return ContextSufficientAcceptEvent(reason=t("agent.thought.no_context_sufficiency_check"))

    prev_queries = await run_context.get("prev_queries", [])
    hop_count = await run_context.get("hop_count", 1)
    more_hops_available = hop_count < max_hops

    async with llm_config.cost_reporting_llm(displayer) as llm:
        guard_result = await context_sufficient_guard(
            llm=llm,
            t=t,
            user_query=user_query,
            context=context,
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
