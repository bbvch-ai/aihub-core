from typing import Annotated

from pydantic import BaseModel, Field


class FilePreviewDTO(BaseModel):
    """An office document as the text a reader sees, for a browser that cannot show the file itself."""

    path: Annotated[str, Field(description="The previewed file, relative to the user's file space.")]
    markdown: Annotated[str, Field(description="The document's content as markdown, without its images.")]
    truncated: Annotated[bool, Field(description="Whether the content was cut short; the download has all of it.")]
