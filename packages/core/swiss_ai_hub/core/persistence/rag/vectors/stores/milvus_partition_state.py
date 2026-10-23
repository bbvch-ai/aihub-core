from enum import StrEnum


class MilvusPartitionState(StrEnum):
    """How a knowledge collection lays out its nodes, read from its manual partitions and creation marker.

    ``COMPLETE`` and ``LEGACY`` never change once observed: partitions are only ever added, and a legacy collection is
    never converted. ``PARTIAL`` is transient — another process may be creating the partitions right now, or its
    creator died mid-way — so it must never be cached.
    """

    COMPLETE = "complete"
    PARTIAL = "partial"
    LEGACY = "legacy"
