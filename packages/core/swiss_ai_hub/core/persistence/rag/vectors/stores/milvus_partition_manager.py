import hashlib

from pymilvus import MilvusClient

# Milvus limit: 1024 total partitions including _default
# So we create 1023 manual partitions (partition_0 to partition_1022)
MAX_PARTITIONS = 1023
DEFAULT_PARTITION_NAME = "_default"
MANUAL_PARTITION_PREFIX = "partition_"
# Written into the schema description, atomically with the collection, so a collection whose creator has not yet
# created any partition is told apart from a legacy one that never gets any.
MANUAL_PARTITIONS_MARKER = f"aihub:manual_partitions:{MAX_PARTITIONS}"


def hash_namespace_to_partition(namespace: str) -> int:
    """MD5 for deterministic uniform distribution. Collisions acceptable since queries filter by namespace."""
    hash_object = hashlib.md5(namespace.encode("utf-8"))
    hash_int = int.from_bytes(hash_object.digest()[:8], byteorder="big")
    return hash_int % MAX_PARTITIONS


def get_partition_name(partition_id: int) -> str:
    if not 0 <= partition_id < MAX_PARTITIONS:
        raise ValueError(f"Partition ID must be in range [0, {MAX_PARTITIONS - 1}], got {partition_id}")
    return f"{MANUAL_PARTITION_PREFIX}{partition_id}"


def create_manual_partitions(client: MilvusClient, collection_name: str) -> None:
    """Create whichever of the 1023 manual partitions are missing.

    Milvus accepts creating a partition that already exists, so a concurrent creator completing the same collection
    is harmless.
    """
    existing = set(client.list_partitions(collection_name=collection_name))
    for partition_id in range(MAX_PARTITIONS):
        partition_name = get_partition_name(partition_id)
        if partition_name not in existing:
            client.create_partition(collection_name=collection_name, partition_name=partition_name)


def get_partition_names_for_namespaces(namespaces: list[str]) -> list[str]:
    return [get_partition_name_for_namespace(namespace) for namespace in namespaces]


def get_partition_name_for_namespace(namespace: str) -> str:
    partition_id = hash_namespace_to_partition(namespace)
    return get_partition_name(partition_id)
