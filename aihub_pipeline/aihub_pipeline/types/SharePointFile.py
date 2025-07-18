from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class MinimalSharePointFile(BaseModel):
    path: Annotated[str, Field(description="Relative path to the file in SharePoint")]
    etag: Annotated[str, Field(description="ETag for change detection")]
    name: Annotated[str, Field(description="File name")]
    id: Annotated[str, Field(description="SharePoint file ID")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[str, Field(description="ISO datetime string when file was last modified")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None


class SharePointFile(BaseModel):
    path: Annotated[str, Field(description="Relative path to the file in SharePoint")]
    content: Annotated[bytes, Field(description="File content as bytes")]
    name: Annotated[str, Field(description="File name")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[str, Field(description="ISO datetime string when file was last modified")]
    created: Annotated[str, Field(description="ISO datetime string when file was created")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    download_url: Annotated[str | None, Field(description="Direct download URL from Graph API")] = None
    full_url: Annotated[str, Field(description="Full SharePoint URL to the file")]

    @property
    def modified_datetime(self) -> datetime:
        return datetime.fromisoformat(self.modified.replace("Z", "+00:00"))

    @property
    def created_datetime(self) -> datetime:
        return datetime.fromisoformat(self.created.replace("Z", "+00:00"))
