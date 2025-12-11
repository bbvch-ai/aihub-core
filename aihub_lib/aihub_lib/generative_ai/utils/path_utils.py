import os
import re

FIGURES_DIRECTORY_NAME = "__figures__"


def create_figures_folder_name(uri: str) -> str:
    """Create a folder name for storing document figures."""
    base_path = os.path.dirname(uri)
    file_name = os.path.basename(uri)
    folder_name = re.sub(r"[\s.%#?&=+]", "_", file_name)
    return f"{base_path}/{FIGURES_DIRECTORY_NAME}/{folder_name}"
