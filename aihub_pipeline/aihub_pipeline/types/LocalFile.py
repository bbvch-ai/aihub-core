from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class MinimalLocalFile(MinimalSourceFile):
    """
    Minimal local file metadata without content.

    This lightweight representation is used by observable assets that scan the local
    file system for changes without reading full file contents. It provides just enough
    metadata to detect changes and determine which files need to be processed.
    """

    pass


class LocalFile(SourceFile, MinimalLocalFile):
    """
    Local file system file implementation of the SourceFile interface.

    Represents a file from the local or network file system, including content,
    metadata, and file system-specific attributes like folder structure.
    """

    pass
