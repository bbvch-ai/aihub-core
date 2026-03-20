import re
from urllib.parse import quote, unquote

FIGURES_DIRECTORY_NAME = "__figures__"


def create_figures_folder_name(uri: str) -> str:
    """Create a folder name for storing document figures."""
    if "/" not in uri:
        raise ValueError(f"Invalid URI, expected at least one '/': {uri}")
    base_path, file_name = uri.rsplit("/", 1)
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        raise ValueError(f"Invalid filename: {file_name}")
    folder_name = re.sub(r"[\s.%#?&=+/\\]", "_", file_name)
    return f"{base_path}/{FIGURES_DIRECTORY_NAME}/{folder_name}"


def encode_partition_key(path: str) -> str:
    """URL-encode a file path for use as a Dagster partition key.

    Reversible via ``decode_partition_key``. Preserves ``/`` separators and ``:`` for URI scheme prefixes.
    """
    return quote(path, safe="/:")


def decode_partition_key(partition_key: str) -> str:
    """Decode a URL-encoded partition key back to the original file path."""
    return unquote(partition_key)
