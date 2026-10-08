from datetime import datetime
from typing import TYPE_CHECKING, Self

from llama_index.core import Document
from pydantic import computed_field
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    HASH,
    INSERTED_AT,
    IS_INGESTED,
    NAMESPACE,
    NODE_CONTENT_TYPE,
    NODE_CONTENT_TYPE_TEXT,
    NODE_TYPE_CONTENT,
    SOURCE,
    SOURCE_ORIGIN,
    TYPE,
    UPDATED_AT,
)

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
    from swiss_ai_hub.pipeline.types.markdown_frontmatter import MarkdownFrontmatter


class RefDocDocument(Document):
    """A Pydantic model representing a specialized Document (llama-index)
    that represents a reference document with additional metadata."""

    @computed_field
    @property
    def namespace(self) -> str:
        return self.metadata.get(NAMESPACE, "")

    @computed_field
    @property
    def hash(self) -> str:
        return self.metadata.get(HASH, "")

    @computed_field
    @property
    def uri(self) -> str:
        return self.metadata.get(SOURCE, "")

    @computed_field
    @property
    def updated(self) -> int:
        return self.metadata.get(UPDATED_AT, int(datetime.now().timestamp()))

    def add_metadata_from_data_lake_file(self, data_lake_file: "DataLakeFile") -> Self:
        """Enrich the document's metadata with information from a `DataLakeFile`."""
        self.id_ = data_lake_file.id_
        uri_parts = data_lake_file.uri.split("/")
        document_title = uri_parts[-1]
        self.metadata = {
            **self.metadata,
            **data_lake_file.metadata,
            NAMESPACE: data_lake_file.metadata.get(NAMESPACE, data_lake_file.namespace),
            HASH: data_lake_file.metadata.get(HASH, data_lake_file.hash),
            UPDATED_AT: int(data_lake_file.metadata.get(UPDATED_AT, data_lake_file.updated)),
            CREATED_AT: int(data_lake_file.metadata.get(CREATED_AT, datetime.now().timestamp())),
            INSERTED_AT: int(datetime.now().timestamp()),  # Convert to current timestamp
            TYPE: NODE_TYPE_CONTENT,
            NODE_CONTENT_TYPE: NODE_CONTENT_TYPE_TEXT,
            SOURCE: data_lake_file.uri,
            SOURCE_ORIGIN: data_lake_file.metadata.get(SOURCE_ORIGIN),
            DOCUMENT_TITLE: data_lake_file.metadata.get(DOCUMENT_TITLE, document_title),
            IS_INGESTED: False,
        }
        return self

    def with_frontmatter(self, frontmatter: "MarkdownFrontmatter") -> Self:
        """A copy whose text is the body, with the frontmatter's fields over the data lake file's.

        The custom keys are left out of the embedded text: they are there to be filtered on, and on a short record
        they would outweigh the body in its vector. Chunks inherit the exclusion from the document.
        """
        document_fields = {
            DOCUMENT_TITLE: frontmatter.title,
            SOURCE_ORIGIN: frontmatter.url,
            CREATED_AT: frontmatter.created,
            UPDATED_AT: frontmatter.updated,
        }
        applied = self.model_copy(
            update={
                "metadata": {
                    **self.metadata,
                    **{key: value for key, value in document_fields.items() if value is not None},
                    **frontmatter.metadata,
                },
                "excluded_embed_metadata_keys": [*self.excluded_embed_metadata_keys, *frontmatter.metadata],
            }
        )
        applied.set_content(frontmatter.body)
        return applied
