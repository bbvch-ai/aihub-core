import logging

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.retrievers.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.insight import InsightEntity


class InsightRetriever(BaseRetriever):
    """Retriever for insights from MongoDB.

    Supports namespace filtering when index_namespaces is set (via NamespaceSelectionAgent flow),
    or retrieves all insights for the agent when index_namespaces is empty (direct flow).
    """

    logger = logging.getLogger(__name__)

    def __init__(self, config: InsightRetrieverConfig) -> None:
        super().__init__(config)
        self.config: InsightRetrieverConfig = config

    @trace_fn
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """
        Retrieve insights for the configured agent, optionally filtered by namespaces.

        When index_namespaces is set, only retrieves insights matching those namespaces.
        When index_namespaces is empty, retrieves all insights for the agent.

        Note: The query parameter is currently unused. This retriever fetches insights
        without semantic filtering.
        """
        try:
            if self.config.index_namespaces:
                insights = InsightEntity.get_by_namespaces_and_agent(
                    namespaces=self.config.index_namespaces,
                    agent_class=self.config.agent_class,
                    agent_id=self.config.agent_id,
                )
            else:
                insights = InsightEntity.get_all_by_agent(
                    agent_class=self.config.agent_class,
                    agent_id=self.config.agent_id,
                )
            return [insight.to_ingested_node(t) for insight in insights]
        except Exception as e:
            self.logger.error(f"Failed to retrieve insights: {e}")
            return []
