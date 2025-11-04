from functools import cache
from pymilvus import MilvusClient, DataType, Function, FunctionType
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.milvus.utils import BM25BuiltInFunction

from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_ID


def create_milvus_vector_store(
    uri: str,
    collection_name: str,
    embedding_vector_dimension: int,
    namespace_field: str = "namespace",
    num_partitions: int = 256,
) -> MilvusVectorStore:
    full_uri = f"{uri}:19530"
    client = MilvusClient(uri=full_uri)

    if not client.has_collection(collection_name):
        schema = client.create_schema(auto_id=False, enable_dynamic_field=True)

        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=65535)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=embedding_vector_dimension)
        schema.add_field("text", DataType.VARCHAR, max_length=65535, enable_analyzer=True)
        schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field(DOCUMENT_ID, DataType.VARCHAR, max_length=65535)
        schema.add_field(namespace_field, DataType.VARCHAR, max_length=512, is_partition_key=True)

        bm25_function = Function(
            name="bm25_fn",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse_embedding"],
            params={},
        )
        schema.add_function(bm25_function)

        index_params = client.prepare_index_params()

        index_params.add_index(field_name="embedding", index_type="AUTOINDEX", metric_type="IP")

        index_params.add_index(field_name="sparse_embedding", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")

        client.create_collection(
            collection_name=collection_name, schema=schema, index_params=index_params, num_partitions=num_partitions
        )

        client.load_collection(collection_name=collection_name)

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
