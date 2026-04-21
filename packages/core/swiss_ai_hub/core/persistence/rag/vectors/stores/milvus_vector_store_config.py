from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field
from pymilvus import MilvusClient

from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.stores.base_pydantic_vector_store_config import (
    BasePydanticVectorStoreConfig,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store


class MilvusVectorStoreConfig(BasePydanticVectorStoreConfig):
    """
    Configuration for Milvus vector store.

    Connection settings (uri, token, dimensions) are read from MilvusSettings at runtime.
    Only collection_name and index_namespaces are stored in the config.

    Supports duality pattern for form rendering and data validation.
    """

    collection_name: Annotated[str, Field(description="Milvus collection name")]
    index_namespaces: Annotated[list[str], Field(description="Namespaces to retrieve from (empty = all)")] = []
    allowed_metadata_filter_fields: Annotated[
        list[str],
        Field(
            description=(
                "Metadata keys that publishers may filter on at query time via `RAGStartEvent.additional_filters`. "
                "The reserved `namespace` key is never allowed."
            )
        ),
    ] = []

    # Override dimensions from base class with default from settings
    # This allows form submissions without dimensions to still validate
    dimensions: Annotated[
        int | InputNumber,
        Field(description="Dimensions of the embeddings (defaults to MilvusSettings.DIMENSION)"),
    ] = Field(default_factory=lambda: MilvusSettings().DIMENSION)

    def to_llama_index(self) -> MilvusVectorStore:
        """Create a MilvusVectorStore instance using connection settings from MilvusSettings."""
        settings = MilvusSettings()
        client = MilvusClient(uri=settings.URL, token=settings.get_token())
        return create_milvus_vector_store(
            client=client,
            collection_name=self.collection_name,
            embedding_vector_dimension=settings.DIMENSION,
            uri=settings.URL,
            token=settings.get_token(),
        )
