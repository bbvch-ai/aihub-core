from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field
from pymilvus import MilvusClient

from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.persistence.rag.vectors.stores import MilvusVectorStoreFactory
from aihub_lib.persistence.rag.vectors.stores.BasePydanticVectorStoreConfig import BasePydanticVectorStoreConfig


class MilvusVectorStoreConfig(BasePydanticVectorStoreConfig):
    """
    Configuration for Milvus vector store.

    Connection settings (uri, token, dimensions) are read from MilvusSettings at runtime.
    Only collection_name and index_namespaces are stored in the config.

    Supports duality pattern for form rendering and data validation.
    """

    collection_name: Annotated[str, Field(description="Milvus collection name")]
    index_namespaces: Annotated[list[str], Field(description="Namespaces to retrieve from (empty = all)")] = []

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
        return MilvusVectorStoreFactory.create_milvus_vector_store(
            client=client,
            collection_name=self.collection_name,
            embedding_vector_dimension=settings.DIMENSION,
            uri=settings.URL,
            token=settings.get_token(),
        )
