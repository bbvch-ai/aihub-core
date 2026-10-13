from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import IngestedNode


class AttachedFileText(BaseModel):
    """An attached file as its sections, whether they came from a fresh read or from the section cache.

    A cached file is never downloaded or parsed again, so what reading by page and the file's event need from the
    document travels here instead of an `ExtractedDocument`.
    """

    sections: Annotated[list[IngestedNode], Field(description="The file split into sections, in document order.")]
    content_sha256: Annotated[
        str, Field(description="Hash of the extracted text, which keys the sections and embeddings of this content.")
    ]
    title: Annotated[str, Field(description="The document's title, or its file name when it has none.")]
    number_of_pages: Annotated[int | None, Field(description="Pages of the document, when its loader knows.")] = None
    is_paged: Annotated[bool, Field(description="Whether its sections carry their page, so pages can be read.")] = False
