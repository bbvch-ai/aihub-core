from typing import Annotated

from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.vectors.stores import AzureAISearchVectorStoreFactory


class AzureAISearchVectorStoreConfig(BaseModel):
    vector_store_name: Annotated[str, Field(description="Azure AI Search vector store name")]
    metadata_fields: Annotated[
        list[str] | None, Field(description="List of metadata fields to be indexed in the vector store")
    ] = None
    language: Annotated[str, Field(description="Language of the documents in the vector store")] = "de"
    semantic_configuration_name: Annotated[
        str, Field(description="Name of the semantic configuration for the vector store")
    ] = "mySemanticConfig"
    dimensions: Annotated[int, Field(description="Dimensions of the embeddings in the vector store")] = 3072

    def to_vector_store(self) -> BasePydanticVectorStore:
        return AzureAISearchVectorStoreFactory.create_azure_ai_search_vector_store(
            vector_store_name=self.vector_store_name,
            metadata_fields=self.metadata_fields,
            language=self.language,
            semantic_configuration_name=self.semantic_configuration_name,
            dimensions=self.dimensions,
        )
