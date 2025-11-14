from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field

from aihub_lib.persistence.rag.vectors.stores import MilvusVectorStoreFactory
from aihub_lib.persistence.rag.vectors.stores.BasePydanticVectorStoreConfig import BasePydanticVectorStoreConfig


class MilvusVectorStoreConfig(BasePydanticVectorStoreConfig):
    uri: Annotated[str, Field(description="Milvus URI")]
    collection_name: Annotated[str, Field(description="Milvus collection name")]

    def to_llama_index(self) -> MilvusVectorStore:
        return MilvusVectorStoreFactory.create_milvus_vector_store(
            uri=self.uri,
            collection_name=self.collection_name,
            embedding_vector_dimension=self.dimensions,
        )
