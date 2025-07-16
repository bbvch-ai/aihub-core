from typing import Annotated

from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.vectors.stores import MilvusVectorStoreFactory


class MilvusVectorStoreConfig(BaseModel):
    uri: Annotated[str, Field(description="Milvus URI")]
    collection_name: Annotated[str, Field(description="Milvus collection name")]
    embedding_vector_dimension: Annotated[int, Field(description="Dimension of the embedding vector")]

    def to_vector_store(self) -> BasePydanticVectorStore:
        return MilvusVectorStoreFactory.create_milvus_vector_store(
            uri=self.uri,
            collection_name=self.collection_name,
            embedding_vector_dimension=self.embedding_vector_dimension,
        )
