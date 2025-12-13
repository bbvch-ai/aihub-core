from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrieval import retrieve_knowledge
from aihub_lib.generative_ai.retrievers import KnowledgeRetrievalOverride, RetrievalOverride
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrievalResponseEvent, RetrievalStartEvent, RetrieverEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.KnowledgeRetrievalAgent.configs.KnowledgeRetrievalAgentConfig import (
    KnowledgeRetrievalAgentConfig,
)
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.rag.steps import execute_order_nodes_by_documents, execute_rerank_nodes
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: KnowledgeRetrievalAgentConfig) -> bool:
    """Precondition to check if reranking is enabled."""
    return isinstance(event, RetrieverEvent) and config.reranking_config.enabled


@precondition()
async def reranking_complete_or_disabled(
    event: RetrieverEvent | RerankerEvent, config: KnowledgeRetrievalAgentConfig
) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    if not config.reranking_config.enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


class KnowledgeRetrievalAgent(Agent):
    """
    Retrieval agent specialized for knowledge (vector store) retrieval.

    This agent retrieves from a single knowledge source with its own
    embedding model and vector store configuration. It is invoked via
    AgentInTheLoop from RAGAgent or ExpertRAGAgent.

    ### Workflow
    1. `retrieve_step`: Retrieves relevant nodes from the knowledge source
    2. `rerank_nodes_step` (conditional): Reranks nodes if reranking is enabled
    3. `order_nodes_by_documents_step`: Orders nodes by their source documents
    4. `stop_step`: Returns the ordered context and raw nodes

    ### Configuration (KnowledgeRetrievalAgentConfig)
    - `retrieval`: Knowledge retrieval step config with embed model, vector store, namespaces
    - `reranking_config`: Configuration for optional reranking
    - `context_prompt`: Optional prompt template for combining nodes
    """

    @step(
        name=LocaleString(en="Retrieve Knowledge Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from the knowledge source."),
    )
    async def retrieve_step(
        self,
        event: RetrievalStartEvent,
        agent_config: KnowledgeRetrievalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes using the step configuration."""
        await displayer.display_thought(t.in_locale(event.locale)("agent.thought.searching_knowledge"))

        namespaces = self._get_namespaces(event.override, agent_config)
        nodes = await retrieve_knowledge(
            query=event.question,
            config=agent_config.retrieval,
            namespaces=namespaces,
        )

        nodes_with_score = [node.to_llama_index_node_with_score() for node in nodes]
        return RetrieverEvent.from_nodes(nodes_with_score)

    def _get_namespaces(
        self,
        override: RetrievalOverride | None,
        config: KnowledgeRetrievalAgentConfig,
    ) -> list[str] | None:
        """Extract namespaces from override or use config defaults."""
        if override is None:
            return None

        if not isinstance(override, KnowledgeRetrievalOverride):
            raise ValueError(
                f"KnowledgeRetrievalAgent expects KnowledgeRetrievalOverride, got {type(override).__name__}"
            )
        return override.namespaces

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
        start_event: RetrievalStartEvent,
        agent_config: KnowledgeRetrievalAgentConfig,
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
        start_event: RetrievalStartEvent,
        agent_config: KnowledgeRetrievalAgentConfig,
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
        name=LocaleString(en="Return Knowledge Retrieval Result"),
        description=LocaleString(en="Returns the ordered nodes as context message."),
    )
    async def stop_step(
        self,
        event: InOrderNodeCombinerEvent,
        retriever_event: RetrieverEvent,
        agent_config: KnowledgeRetrievalAgentConfig,
    ) -> RetrievalResponseEvent:
        """Returns the retrieval result with context message, raw nodes, and agent ID."""
        return RetrievalResponseEvent(
            context_message=event.context_message,
            nodes=retriever_event.nodes,
            agent_id=agent_config.agent_id,
            retrieval_type="knowledge",
        )
