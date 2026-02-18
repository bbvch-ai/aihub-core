import re

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
