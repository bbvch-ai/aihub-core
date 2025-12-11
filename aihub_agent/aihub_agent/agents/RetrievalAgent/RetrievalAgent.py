from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from aihub_agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.rag.steps import (
    execute_order_nodes_by_documents,
    execute_rerank_nodes,
    execute_retrieve,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: RetrievalAgentConfig) -> bool:
    """Precondition to check if reranking is enabled."""
    return isinstance(event, RetrieverEvent) and config.reranking_config.enabled


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RetrievalAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    if not config.reranking_config.enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


class RetrievalAgent(Agent):
    """
    Retrieval agent that encapsulates the retrieval pipeline: retrieve → rerank → order.

    This agent is invoked via AgentInTheLoop from RAGAgent or ExpertRAGAgent
    to share retrieval logic. It must be registered with its own RetrievalAgentConfig
    containing the retriever and reranking settings.

    ### Workflow
    1. `retrieve_step`: Retrieves relevant nodes from multiple sources in parallel
    2. `rerank_nodes_step` (conditional): Reranks nodes if reranking is enabled
    3. `order_nodes_by_documents_step`: Orders nodes by their source documents
    4. `stop_step`: Returns the ordered context and raw nodes

    ### Configuration (RetrievalAgentConfig)
    - `retrievers`: List of retriever configurations (KnowledgeRetrieverConfig, InsightRetrieverConfig)
    - `reranking_config`: Configuration for optional reranking
    - `context_prompt`: Optional prompt template for combining nodes
    """

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: QuestionStartEvent,
        agent_config: RetrievalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        return await execute_retrieve(
            query=event.question,
            retrievers=agent_config.retrievers,
            displayer=displayer,
            t=t.in_locale(event.locale),
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
        start_event: QuestionStartEvent,
        agent_config: RetrievalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RerankerEvent:
        """Reranks retrieved documents using a dedicated reranking model."""
        return await execute_rerank_nodes(
            nodes=event.nodes,
            query=start_event.question,
            reranking_model=agent_config.reranking_config.reranking_model,
            displayer=displayer,
            t=t.in_locale(start_event.locale),
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
        start_event: QuestionStartEvent,
        agent_config: RetrievalAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        """Orders the retrieved nodes based on their source documents."""
        nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
        return await execute_order_nodes_by_documents(
            nodes=nodes,
            t=t.in_locale(start_event.locale),
            displayer=displayer,
            context_prompt=agent_config.context_prompt,
        )

    @step(
        name=LocaleString(en="Return Retrieval Result"),
        description=LocaleString(en="Returns the ordered nodes as context message."),
    )
    async def stop_step(
        self,
        event: InOrderNodeCombinerEvent,
        retriever_event: RetrieverEvent,
    ) -> RetrievalResponseEvent:
        """Returns the retrieval result with context message and raw nodes."""
        return RetrievalResponseEvent(context_message=event.context_message, nodes=retriever_event.nodes)
