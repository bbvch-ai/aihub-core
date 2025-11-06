from abc import ABC, abstractmethod
from datetime import datetime


class MinimalSourceFile(ABC):
    """
    Minimal interface for source file metadata without content.

    This lightweight interface is used when only metadata is needed (e.g., for
    comparing source files with data lake files to determine which files to remove).
    It excludes the potentially large file content to improve performance when
    processing large numbers of files.

    This is commonly used by observable assets that scan source systems for changes
    without downloading full file contents.
    """

    @property
    @abstractmethod
    def path(self) -> str:
        """
        Relative path within the source system.
        """
        pass


class SourceFile(ABC):
    """
    Generic interface for files from any source system.

    This abstract base class defines the common interface that all source file types
    (SharePoint, local file system, cloud storage, etc.) must implement. It ensures
    that downstream pipeline operations can work with files from any source without
    needing source-specific logic.

    The interface provides access to:
    - File content and metadata (name, path, size)
    - Temporal information (created, modified timestamps)
    - Source origin information (URL or path in the source system)

    Example implementations:
        - SharePointFile: Files retrieved from Microsoft SharePoint
        - FileSystemFile: Files from local or network file systems
        - S3File: Files from AWS S3 buckets
    """

    @property
    @abstractmethod
    def content(self) -> bytes:
        """
        File content as raw bytes.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        File name including extension.
        """
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        """
        Relative path within the source system.

        This should be the path relative to the source system's root or
        configured base directory. Used to maintain directory structure
        when ingesting into the data lake.
        """
        pass

    @property
    @abstractmethod
    def source_url(self) -> str:
        """
        Full URL or path in the source system.

        This is the canonical reference to the file in its source system,
        used for tracking file origin and providing links back to the source.
        """
        pass

    @property
    @abstractmethod
    def modified_datetime(self) -> datetime:
        """
        Last modified timestamp.
        """
        pass

    @property
    @abstractmethod
    def created_datetime(self) -> datetime:
        """
        Creation timestamp.
        """
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """
        File size in bytes.
        """
        pass
