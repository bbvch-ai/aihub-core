from functools import cache

from llama_index.vector_stores.milvus import MilvusVectorStore


@cache
def create_milvus_vector_store(uri: str, collection_name: str, embedding_vector_dimension: int) -> MilvusVectorStore:
    return MilvusVectorStore(
        uri=uri,
        port="19530",
        collection_name=collection_name,
        dim=embedding_vector_dimension,
        overwrite=False,
    )
