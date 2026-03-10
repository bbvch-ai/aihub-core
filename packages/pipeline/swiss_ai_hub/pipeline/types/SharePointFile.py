from typing import Annotated

from pydantic import Field

from swiss_ai_hub.pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class MinimalSharePointFile(MinimalSourceFile):
    """
    Minimal SharePoint file metadata without content.

    Used for scanning SharePoint for changes without downloading full file contents.
    Includes SharePoint-specific fields like ETag and file ID for change detection.
    """

    etag: Annotated[str, Field(description="ETag for change detection")]
    id: Annotated[str, Field(description="SharePoint file ID")]
    created: Annotated[int, Field(description="The UNIX timestamp when the file was created")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None


class SharePointFile(SourceFile):
    """
    SharePoint file implementation of the SourceFile interface.

    Represents a file retrieved from Microsoft SharePoint via the Graph API,
    including content, metadata, and SharePoint-specific attributes like ETags
    and download URLs.
    """

    download_url: Annotated[str | None, Field(description="Direct download URL from Graph API")] = None
    full_url: Annotated[str, Field(description="Full SharePoint web URL to the file")]

    @property
    def source_url(self) -> str:
        """Returns the full SharePoint web URL as the source URL."""
        return self.full_url
