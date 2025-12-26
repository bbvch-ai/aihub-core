from typing import Annotated

from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field
from pymilvus import MilvusClient

from aihub_lib.persistence.rag.vectors.stores import MilvusVectorStoreFactory
from aihub_lib.persistence.rag.vectors.stores.BasePydanticVectorStoreConfig import BasePydanticVectorStoreConfig


class MilvusVectorStoreConfig(BasePydanticVectorStoreConfig):
    uri: Annotated[str, Field(description="Milvus URI")]
    collection_name: Annotated[str, Field(description="Milvus collection name")]

    def to_llama_index(self) -> MilvusVectorStore:
        client = MilvusClient(uri=self.uri)
        return MilvusVectorStoreFactory.create_milvus_vector_store(
            client=client,
            collection_name=self.collection_name,
            embedding_vector_dimension=self.dimensions,
        )
