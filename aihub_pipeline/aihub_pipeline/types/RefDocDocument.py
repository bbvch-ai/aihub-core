from datetime import datetime
from typing import TYPE_CHECKING, Self

from aihub_lib.persistence.rag.vectors.node_metadata import (
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
from llama_index.core import Document
from pydantic import computed_field

if TYPE_CHECKING:
    from aihub_pipeline.types.DataLakeFile import DataLakeFile


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
            IS_INGESTED: True,
        }
        return self
