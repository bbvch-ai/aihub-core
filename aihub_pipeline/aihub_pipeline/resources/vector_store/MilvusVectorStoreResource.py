from dagster import ConfigurableResource, InitResourceContext
from aihub_lib.persistence.rag.vectors.vector_stores.MilvusVectorStoreFactory import create_milvus_vector_store
from llama_index.vector_stores.milvus import MilvusVectorStore


class MilvusVectorStoreResource(ConfigurableResource[MilvusVectorStore]):
    uri: str
    collection_name: str
    embedding_vector_dimension: int

    def create_resource(self, context: InitResourceContext) -> MilvusVectorStore:
        return create_milvus_vector_store(
            self.uri, self.collection_name, self.embedding_vector_dimension
        )
