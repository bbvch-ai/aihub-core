from typing import Annotated

from pydantic import BaseModel, Field


class AttachedFileRecord(BaseModel):
    """What the section cache remembers about one upload, so its next read needs neither the file nor its parse."""

    content_sha256: Annotated[str, Field(description="Hash of the upload's extracted text, keying its sections.")]
    title: Annotated[str, Field(description="The document's title, or its file name when it has none.")]
    number_of_pages: Annotated[int | None, Field(description="Pages of the document, when its loader knows.")] = None
    is_paged: Annotated[bool, Field(description="Whether the document can be read by page.")] = False
