from typing import Annotated

from pydantic import Field

from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile, SourceFile


class MinimalRcloneFile(MinimalSourceFile):
    """
    Minimal rclone file metadata without content.

    Used for scanning rclone sources for changes without downloading full file contents.
    Works with any rclone-supported backend (OneDrive, SharePoint, S3, Azure, Google Drive, etc.).
    """

    remote: Annotated[str, Field(description="Rclone remote name (e.g., 'onedrive:', 'sharepoint:')")] = ""
    is_dir: Annotated[bool, Field(description="Whether this is a directory")] = False
    mime_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    id: Annotated[str | None, Field(description="Remote-specific file ID if available")] = None
    hashes: Annotated[
        dict[str, str] | None,
        Field(description="Hash checksums from remote backend (e.g., {'md5': '...', 'sha1': '...'})"),
    ] = None
    created: Annotated[int, Field(description="The UNIX timestamp when the file was created (birth time)")] = 0


class RcloneFile(SourceFile, MinimalRcloneFile):
    """
    Rclone file implementation of the SourceFile interface.

    Represents a file retrieved from any rclone-supported backend (OneDrive, SharePoint,
    S3, Azure Blob, Google Drive, Dropbox, Box, local filesystem, etc.).

    This generic implementation works with all 70+ rclone backends without requiring
    backend-specific code.
    """

    remote_path: Annotated[str, Field(description="Full path within the remote")]

    @property
    def source_url(self) -> str:
        """Returns the rclone-style URL (remote:path)."""
        return f"{self.remote}{self.remote_path}"
