from collections.abc import Callable

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.chat_history.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.chat_history.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
from aihub_lib.generative_ai.guards.few_shot_guard import few_shot_guard
from aihub_lib.generative_ai.rerank.rerank_nodes import rerank_nodes
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
from aihub_lib.generative_ai.retrieval.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.retrieval.retrieve_from_all_sources import retrieve_from_all_sources
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import LimitChatHistoryEvent, StandaloneQuestionCondenserEvent
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMEvent, LLMStopEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pymilvus import MilvusClient

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.context.run.RunContext import RunContext


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
    retrievers: list[KnowledgeRetrieverConfig],
    t: LocaleHandler,
    milvus_client: MilvusClient | None = None,
) -> RetrieverEvent:
    """Retrieve nodes from all sources and return RetrieverEvent."""
    if isinstance(event, StandaloneQuestionCondenserEvent):
        query = event.condensed_chat_message.content or ""
    else:
        query = event.new_query
    all_nodes = await retrieve_from_all_sources(query, retrievers, t, milvus_client=milvus_client)
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
        reranked=reranking_config.enabled,
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
) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
    """Execute context sufficient guard with hop management."""
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
