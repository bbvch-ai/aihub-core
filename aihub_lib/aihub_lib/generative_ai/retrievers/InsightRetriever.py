import logging

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.retrievers.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.insight import InsightEntity


class InsightRetriever(BaseRetriever):
    """Retriever for insights from MongoDB."""

    logger = logging.getLogger(__name__)

    def __init__(self, config: InsightRetrieverConfig) -> None:
        super().__init__(config)
        self.config: InsightRetrieverConfig = config

    @trace_fn
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """
        Retrieve all insights for the configured namespace and agent.

        Note: The query parameter is currently unused. This retriever fetches all
        insights for the configured namespace/agent without semantic filtering.
        """
        try:
            insights = InsightEntity.get_by_namespace_and_agent(
                namespace=self.config.namespace,
                agent_class=self.config.agent_class,
                agent_id=self.config.agent_id,
            )
            return [insight.to_ingested_node(t) for insight in insights]
        except Exception as e:
            self.logger.error(f"Failed to retrieve insights: {e}")
            return []
