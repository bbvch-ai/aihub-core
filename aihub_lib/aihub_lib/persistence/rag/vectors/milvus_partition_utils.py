import hashlib


def namespace_to_partition_key(namespace: str) -> str:
    """
    Convert a namespace string to a valid Milvus partition name using SHA256 hash.
    Examples:
        >>> namespace_to_partition_key("customer-a")
        'ns_8f14e45fceea167a5a36dedd4bea2543'
    """
    return f"ns_{hashlib.sha256(namespace.encode()).hexdigest()}"
