import logging

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers import InsightSourceConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.insight import InsightEntity

logger = logging.getLogger(__name__)


@trace_fn
async def retrieve_insights(
    sources: list[InsightSourceConfig],
    t: LocaleHandler,
) -> list[IngestedNode]:
    """
    Retrieve insights from MongoDB for the given sources.

    Args:
        sources: List of insight sources (namespace, agent_class, agent_id) to query
        t: Locale handler for translations

    Returns:
        List of retrieved insight nodes
    """
    all_nodes: list[IngestedNode] = []

    for source in sources:
        try:
            insights = InsightEntity.get_by_namespace_and_agent(
                namespace=source.namespace,
                agent_class=source.agent_class,
                agent_id=source.agent_id,
            )
            nodes = [_insight_to_node(insight, t) for insight in insights]
            all_nodes.extend(nodes)
        except Exception as e:
            logger.error(f"Failed to retrieve insights from {source}: {e}")

    return all_nodes


def _insight_to_node(insight: InsightEntity, t: LocaleHandler) -> IngestedNode:
    """Convert an InsightEntity to an IngestedNode."""
    conversation_lines = [f"{t(f'lib.insight.role.{msg.role.value}')}: {msg.content}" for msg in insight.conversation]
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
