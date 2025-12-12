from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrieval import retrieve_insights
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.InsightRetrievalAgent.configs.InsightRetrievalAgentConfig import InsightRetrievalAgentConfig
from aihub_agent.agents.InsightRetrievalAgent.events.InsightRetrievalResponseEvent import InsightRetrievalResponseEvent
from aihub_agent.agents.InsightRetrievalAgent.events.InsightRetrievalStartEvent import InsightRetrievalStartEvent
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.rag.steps import execute_order_nodes_by_documents
from aihub_agent.workflow.decorators.step import step


class InsightRetrievalAgent(Agent):
    """
    Retrieval agent specialized for insight (MongoDB) retrieval.

    This agent retrieves expert-provided insights from MongoDB. It is invoked
    via AgentInTheLoop from RAGAgent or ExpertRAGAgent.

    Note: No reranking is applied for insights as they are curated knowledge.

    ### Workflow
    1. `retrieve_step`: Retrieves insights from configured sources
    2. `order_nodes_by_documents_step`: Orders nodes by their source documents
    3. `stop_step`: Returns the ordered context and raw nodes

    ### Configuration (InsightRetrievalAgentConfig)
    - `retrieval`: Insight retrieval step config with default sources
    - `context_prompt`: Optional prompt template for combining nodes
    """

    @step(
        name=LocaleString(en="Retrieve Insights"),
        description=LocaleString(en="Retrieves insights from configured sources."),
    )
    async def retrieve_step(
        self,
        event: InsightRetrievalStartEvent,
        agent_config: InsightRetrievalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves insights using the step configuration."""
        locale_t = t.in_locale(event.locale)
        await displayer.display_thought(locale_t("agent.thought.searching_insights"))

        # Use event sources if provided, otherwise fall back to step config
        sources = event.sources or agent_config.retrieval.sources

        nodes = await retrieve_insights(sources=sources, t=locale_t)

        nodes_with_score = [node.to_llama_index_node_with_score() for node in nodes]
        return RetrieverEvent.from_nodes(nodes_with_score)

    @step(
        name=LocaleString(en="Order Nodes by Documents"),
        description=LocaleString(en="Orders the retrieved nodes by their source documents."),
    )
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent,
        start_event: InsightRetrievalStartEvent,
        agent_config: InsightRetrievalAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        """Orders the retrieved nodes based on their source documents."""
        return await execute_order_nodes_by_documents(
            nodes=event.nodes,
            t=t.in_locale(start_event.locale),
            displayer=displayer,
            context_prompt=agent_config.context_prompt,
        )

    @step(
        name=LocaleString(en="Return Insight Retrieval Result"),
        description=LocaleString(en="Returns the ordered nodes as context message."),
    )
    async def stop_step(
        self,
        event: InOrderNodeCombinerEvent,
        retriever_event: RetrieverEvent,
    ) -> InsightRetrievalResponseEvent:
        """Returns the retrieval result with context message and raw nodes."""
        return InsightRetrievalResponseEvent(
            context_message=event.context_message,
            nodes=retriever_event.nodes,
        )
