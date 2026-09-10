from typing import Annotated, Self

from llama_index.core.schema import Document
from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.extraction.document_title_deriver import DocumentTitleDeriver
from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import SUBJECT
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NUMBER_OF_PAGES


class ExtractedDocument(BaseModel):
    """A document reduced to the two things a content-understanding workflow needs — a title and a body."""

    title: Annotated[str, Field(description="Email subject, first heading, or filename stem.")]
    content: Annotated[str, Field(description="Extracted body text as markdown.")]
    content_type: Annotated[str, Field(description="MIME type, from the caller or guessed from the filename.")]
    source_filename: Annotated[str, Field(description="Filename the content was read as.")]
    document_parser: Annotated[str, Field(description="Loader class that produced the content.")]
    number_of_pages: Annotated[int | None, Field(description="Page count where the loader reports one.")] = None
    source: Annotated[str | None, Field(description="`s3://bucket/key` it was read from, when read from S3.")] = None

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        filename: str,
        content_type: str,
        document_parser: str,
        source: str | None = None,
    ) -> Self:
        """Fold a loader's documents into one result.

        Every loader here returns a single whole-document `Document`, but the signature is a list, so joining rather
        than indexing `[0]` keeps this correct for a loader that ever splits.
        """
        content = "\n\n".join(document.text for document in documents).strip()
        metadata = documents[0].metadata if documents else {}
        return cls(
            title=DocumentTitleDeriver.derive(content, filename, subject=metadata.get(SUBJECT)),
            content=content,
            content_type=content_type,
            source_filename=filename,
            document_parser=document_parser,
            number_of_pages=metadata.get(NUMBER_OF_PAGES),
            source=source,
        )
