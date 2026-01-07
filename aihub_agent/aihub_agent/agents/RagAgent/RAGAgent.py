from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.generative_ai.retrievers.RetrieverConfig import RetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
)
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.events.BucketNamespacePair import BucketNamespacePair
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.RagAgent.events.NamespaceAwareStartEvent import NamespaceAwareStartEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.preconditions import (
    check_context_ready_for_history_limit,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
)
from aihub_agent.rag.step_functions import (
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
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step

SELECTED_NAMESPACES_KEY = "_selected_namespaces"


def _filter_retrievers_by_namespace(
    retrievers: list[RetrieverConfig],
    selected_namespaces: list[BucketNamespacePair],
) -> list[RetrieverConfig]:
    if not selected_namespaces:
        return retrievers

    namespace_map = {pair.bucket_name: pair.namespace_name for pair in selected_namespaces}

    filtered: list[RetrieverConfig] = []
    for retriever in retrievers:
        if isinstance(retriever, KnowledgeRetrieverConfig):
            bucket_name = retriever.vector_store.collection_name
            if bucket_name in namespace_map:
                selected_namespace = namespace_map[bucket_name]
                if selected_namespace in retriever.index_namespaces:
                    filtered_retriever = retriever.model_copy(update={"index_namespaces": [selected_namespace]})
                    filtered.append(filtered_retriever)
        else:
            # Pass through non-knowledge retrievers (e.g., InsightRetrieverConfig) unchanged
            filtered.append(retriever)
    return filtered


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: RAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config.enabled)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config.enabled)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when InOrderNodeCombinerEvent is present AND ContextSufficientAcceptEvent is present.
    """
    return check_context_ready_for_history_limit(context_event, context_sufficient_event)


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent | NamespaceAwareStartEvent,
        agent_config: RAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        if isinstance(event, NamespaceAwareStartEvent):
            await run_context.set(SELECTED_NAMESPACES_KEY, [ns.model_dump() for ns in event.selected_namespaces])
        return do_limit_chat_history(event.messages, agent_config.number_of_input_tokens)

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent | NamespaceAwareStartEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        return await do_condense_standalone_question(
            event.limited_history, start_event.last_user_message, agent_config.llm, displayer, t
        )

    @step(
        name=LocaleString(en="Few Shot Guard"),
        description=LocaleString(en="Guards the question to ensure it is appropriate for the agent to answer."),
    )
    async def few_shot_guard_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            event.condensed_chat_message.content, agent_config.few_shot_guard_examples, agent_config.llm, displayer, t
        )

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        agent_config: RAGAgentConfig,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        selected_namespaces_raw = await run_context.get(SELECTED_NAMESPACES_KEY, [])
        selected_namespaces = [BucketNamespacePair(**ns) for ns in selected_namespaces_raw]
        filtered_retrievers = _filter_retrievers_by_namespace(agent_config.retrievers, selected_namespaces)
        return await do_retrieve(event, filtered_retrievers, t)

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
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RerankerEvent:
        return await do_rerank_nodes(
            event.nodes, condense_event.condensed_chat_message.content, agent_config.reranking_config, displayer, t
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
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        return await do_order_nodes_by_documents(event, t, agent_config.context_prompt, displayer)

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: InOrderNodeCombinerEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        return await do_context_sufficient_guard(
            user_query_event.condensed_chat_message.content,
            event.context_message.content,
            agent_config.check_context_sufficiency,
            agent_config.max_hops,
            run_context,
            agent_config.llm,
            displayer,
            t,
        )

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | NamespaceAwareStartEvent,
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
        name=LocaleString(en="Respond with LLM"),
        description=LocaleString(en="Generates a response using the configured LLM."),
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        return await do_respond_with_llm(
            event,
            limited_history_without_context.limited_history,
            agent_config.context_insufficient_prompt,
            agent_config.system_prompt,
            agent_config.llm,
            displayer,
            t,
        )
