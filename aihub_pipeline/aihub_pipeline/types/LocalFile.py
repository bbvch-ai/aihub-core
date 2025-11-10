from typing import Annotated

from pydantic import ConfigDict, Field

from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class MinimalLocalFile(MinimalSourceFile):
    """
    Minimal local file metadata without content.

    This lightweight representation is used by observable assets that scan the local
    file system for changes without reading full file contents. It provides just enough
    metadata to detect changes and determine which files need to be processed.
    """

    model_config = ConfigDict(populate_by_name=True)

    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name within source folder")] = None


class LocalFile(SourceFile):
    """
    Local file system file implementation of the SourceFile interface.

    Represents a file from the local or network file system, including content,
    metadata, and file system-specific attributes like folder structure.
    """

    model_config = ConfigDict(populate_by_name=True)

    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name within source folder")] = None
