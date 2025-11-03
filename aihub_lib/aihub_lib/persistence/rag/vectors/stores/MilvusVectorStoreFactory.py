from functools import cache

from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.milvus.utils import BM25BuiltInFunction

from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_ID


@cache
def create_milvus_vector_store(uri: str, collection_name: str, embedding_vector_dimension: int) -> MilvusVectorStore:
    return MilvusVectorStore(
        uri=uri,
        port="19530",
        collection_name=collection_name,
        dim=embedding_vector_dimension,
        overwrite=False,
        doc_id_field=DOCUMENT_ID,
        enable_sparse=True,
        sparse_embedding_function=BM25BuiltInFunction(),
    )
