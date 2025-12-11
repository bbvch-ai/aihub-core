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
            return [self._insight_to_node(insight, t) for insight in insights]
        except Exception as e:
            self.logger.error(f"Failed to retrieve insights: {e}")
            return []

    def _insight_to_node(self, insight: InsightEntity, t: LocaleHandler) -> IngestedNode:
        """Convert an InsightEntity to an IngestedNode."""
        conversation_lines = [
            f"{t(f'lib.insight.role.{msg.role.value}')}: {msg.content}" for msg in insight.conversation
        ]
        content_parts: list[str] = [
            f"{t('lib.insight.label.question')}: {insight.question}",
            f"{t('lib.insight.label.answer')}: {insight.expert_answer}",
            f"{t('lib.insight.label.conversation')}:",
            *conversation_lines,
        ]

        content: str = "\n".join(content_parts)

        created_at: str = insight.created_at.isoformat().replace("+00:00", "Z")
        updated_at: str = insight.updated_at.isoformat().replace("+00:00", "Z")

        return IngestedNode(
            id=str(insight.id),
            content=content,
            document_id=str(insight.id),
            source=f"insight:{insight.id}",
            source_origin=insight.source.thread_id,
            namespace=insight.namespace,
            document_title=insight.question[:100],
            created_at=created_at,
            updated_at=updated_at,
            inserted_at=created_at,
            metadata={
                "insight_type": "expert_conversation",
                "expert_user_id": insight.source.expert_user_id,
                "expert_name": insight.source.expert_name,
                "agent_class": insight.creator.agent_class,
                "agent_id": insight.creator.agent_id,
            },
        )
