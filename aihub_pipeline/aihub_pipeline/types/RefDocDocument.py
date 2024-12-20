from datetime import datetime
from typing import TYPE_CHECKING

from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DATA_LAKE_URI,
    HASH,
    INSERTED_AT,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    TYPE,
    UPDATED_AT,
)
from llama_index.core import Document
from pydantic import computed_field

if TYPE_CHECKING:
    from aihub_pipeline.types.DataLakeFile import DataLakeFile


class RefDocDocument(Document):
    """A Pydantic model representing specialized Document (llama-index)
    that represents a reference document with additional metadata."""

    @computed_field
    @property
    def namespace(self) -> str:
        return self.metadata[NAMESPACE]

    @computed_field
    @property
    def hash(self) -> str:
        return self.metadata[HASH]

    @computed_field
    @property
    def uri(self) -> str:
        return self.metadata[DATA_LAKE_URI]

    @computed_field
    @property
    def updated(self) -> int:
        return self.metadata[UPDATED_AT]

    def add_metadata_from_data_lake_file(
        self, data_lake_file: "DataLakeFile"
    ) -> "RefDocDocument":
        """Enrich the document's metadata with information from a `DataLakeFile`."""
        self.id_ = data_lake_file.id_
        self.metadata = {
            **self.metadata,
            **data_lake_file.metadata,
            NAMESPACE: data_lake_file.namespace,
            HASH: data_lake_file.hash,
            UPDATED_AT: data_lake_file.updated,
            CREATED_AT: int(
                data_lake_file.metadata.get(CREATED_AT, datetime.now().timestamp())
            ),
            INSERTED_AT: int(
                datetime.now().timestamp()
            ),  # Convert to current timestamp
            TYPE: NODE_TYPE_CONTENT,
            DATA_LAKE_URI: data_lake_file.uri,
        }
        return self
