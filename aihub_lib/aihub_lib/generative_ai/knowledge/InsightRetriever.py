"""Retriever implementation using MongoDB text search for insights."""

from datetime import UTC, datetime

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.knowledge.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.knowledge.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.insight.InsightEntity import InsightEntity
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_TEXT, NODE_TYPE_CONTENT


class InsightRetriever(BaseRetriever):
    """
    Retriever implementation using MongoDB text search for insights.

    Uses InsightEntity.search_insights() which leverages MongoDB's
    text search index on title + content fields. No vector embeddings
    required - simple and fast for structured expert knowledge.
    """

    def __init__(self, config: InsightRetrieverConfig) -> None:
        super().__init__(config)
        self._config = config

    @trace_fn
    async def retrieve(self, query: str) -> list[IngestedNode]:
        """
        Retrieve relevant insights using MongoDB text search.

        Args:
            query: The search query string

        Returns:
            List of IngestedNode objects created from matching insights
        """
        insights, _ = InsightEntity.search_insights(
            search_text=query,
            namespace=self._config.namespace,
            page=1,
            page_size=self._config.max_results,
        )

        return [self._insight_to_node(insight) for insight in insights]

    def _insight_to_node(self, insight: InsightEntity) -> IngestedNode:
        """Convert an InsightEntity to an IngestedNode for consistent handling."""
        now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        created = insight.created_at.isoformat().replace("+00:00", "Z") if insight.created_at else now_iso
        updated = insight.updated_at.isoformat().replace("+00:00", "Z") if insight.updated_at else now_iso

        # Build content with title, content, and optionally expert answer
        full_content = f"**{insight.title}**\n\n{insight.content}"
        if insight.expert_answer:
            full_content += f"\n\n**Expert Answer:** {insight.expert_answer}"

        return IngestedNode(
            id=str(insight.id),
            content=full_content,
            type=NODE_TYPE_CONTENT,
            content_type=NODE_CONTENT_TYPE_TEXT,
            document_id=str(insight.id),
            source=f"insight://{insight.namespace or 'default'}/{insight.id}",
            source_origin=None,
            namespace=insight.namespace or "default",
            document_title=insight.title,
            created_at=created,
            updated_at=updated,
            inserted_at=created,
            score=0.5,  # Default score for text search results
            metadata={"tags": insight.tags or [], "question": insight.question},
        )
