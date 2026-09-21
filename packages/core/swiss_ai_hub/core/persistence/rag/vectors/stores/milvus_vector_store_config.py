from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field, model_validator
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
    Only the collection, its namespace scope and the allowed filter fields are stored in the config.

    The namespace scope is explicit: either name the namespaces to read or opt into every namespace with
    ``all_namespaces``. An empty list without that flag is rejected rather than silently widened to the
    whole collection, so nobody grants an agent more than they saw in the editor.

    Supports duality pattern for form rendering and data validation.
    """

    collection_name: Annotated[str, Field(description="Milvus collection name")]
    index_namespaces: Annotated[
        list[str], Field(description="Namespaces to retrieve from; leave empty only together with all_namespaces")
    ] = []
    all_namespaces: Annotated[
        bool,
        Field(
            description="Read every namespace of the collection, including ones created later. "
            "Mutually exclusive with naming namespaces."
        ),
    ] = False
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

    @model_validator(mode="after")
    def _namespace_scope_is_explicit(self) -> "MilvusVectorStoreConfig":
        if self.all_namespaces and self.index_namespaces:
            raise ValueError("Either name the namespaces to search or enable all_namespaces, not both.")
        if not self.all_namespaces and not self.index_namespaces:
            raise ValueError("Select at least one namespace to search, or enable all_namespaces.")
        return self

    @property
    def namespace_filter(self) -> list[str] | None:
        """Namespaces to restrict retrieval to; ``None`` means the whole collection."""
        return None if self.all_namespaces else self.index_namespaces

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
