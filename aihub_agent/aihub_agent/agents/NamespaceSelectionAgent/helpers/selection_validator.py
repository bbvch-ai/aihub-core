"""
Namespace selection validation for NamespaceSelectionAgent.

Provides validation to ensure exactly one namespace per allowed bucket.
"""

import logging

from aihub_lib.nats.events import KnowledgeSource

from aihub_agent.agents.NamespaceSelectionAgent.helpers.namespace_selector import AvailableNamespace

logger = logging.getLogger(__name__)


def normalize_selection(
    sources: list[KnowledgeSource],
    available: list[AvailableNamespace],
    allowed_buckets: list[str],
) -> list[KnowledgeSource]:
    """
    Ensure exactly one namespace per allowed bucket.

    - Removes duplicate selections (keeps first per bucket)
    - Fills missing buckets with first available namespace

    Args:
        sources: LLM-selected knowledge sources.
        available: All available namespaces.
        allowed_buckets: Bucket names that must be covered.

    Returns:
        Normalized list with exactly one namespace per allowed bucket.
    """
    # Dedupe: keep first selection per bucket
    by_bucket: dict[str, KnowledgeSource] = {}
    for source in sources:
        if source.bucket_name in by_bucket:
            logger.debug(
                f"Multiple namespaces selected for bucket {source.bucket_name}, "
                f"keeping {by_bucket[source.bucket_name].namespace_name}"
            )
        else:
            by_bucket[source.bucket_name] = source

    # Fill missing buckets
    for bucket in allowed_buckets:
        if bucket not in by_bucket:
            for ns in available:
                if ns.bucket_name == bucket:
                    by_bucket[bucket] = KnowledgeSource(
                        bucket_name=bucket,
                        namespace_name=ns.namespace_name,
                        display_name=ns.display_name,
                    )
                    logger.info(f"Auto-selected {ns.namespace_name} for uncovered bucket {bucket}")
                    break

    return list(by_bucket.values())
