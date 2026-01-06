"""
Namespace selection validation for NamespaceSelectionAgent.

Provides validation functions to ensure namespace selections meet
the one-per-bucket constraint and all allowed buckets are covered.
"""

import logging

from aihub_lib.nats.events import KnowledgeSource

from aihub_agent.agents.NamespaceSelectionAgent.helpers.namespace_selector import AvailableNamespace

logger = logging.getLogger(__name__)


def validate_one_per_bucket(sources: list[KnowledgeSource]) -> list[KnowledgeSource]:
    """
    Ensure exactly one namespace per bucket.

    If multiple namespaces from the same bucket are selected,
    keeps only the first one encountered.
    """
    by_bucket: dict[str, KnowledgeSource] = {}
    for source in sources:
        if source.bucket_name in by_bucket:
            logger.warning(
                f"Multiple namespaces selected for bucket {source.bucket_name}, "
                f"keeping {by_bucket[source.bucket_name].namespace_name}"
            )
        else:
            by_bucket[source.bucket_name] = source
    return list(by_bucket.values())


def ensure_all_buckets_covered(
    sources: list[KnowledgeSource],
    available: list[AvailableNamespace],
    allowed_buckets: list[str],
) -> list[KnowledgeSource]:
    """
    Ensure each allowed bucket has a selected namespace.

    If a bucket has no selection, picks the first available namespace
    from that bucket as a fallback.
    """
    result = list(sources)  # Don't modify original
    covered = {s.bucket_name for s in result}

    for bucket in allowed_buckets:
        if bucket not in covered:
            # Find first available namespace in this bucket
            for ns in available:
                if ns.bucket_name == bucket:
                    result.append(
                        KnowledgeSource(
                            bucket_name=bucket,
                            namespace_name=ns.namespace_name,
                            display_name=ns.display_name,
                        )
                    )
                    logger.info(f"Auto-selected {ns.namespace_name} for uncovered bucket {bucket}")
                    break

    return result
