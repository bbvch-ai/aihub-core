from dagster import ConfigurableResource, InitResourceContext
from llama_index.vector_stores.milvus import MilvusVectorStore

from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_resource_init
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store


class RoutedMilvusVectorStoreResource(ConfigurableResource[MilvusVectorStore]):
    """Per-run Milvus vector store for the RAG pipeline, scoped to the run's bucket's collection.

    Resolves the collection name from the ``aihub/bucket`` run tag so the RAG pipeline can delete
    a removed document's nodes from any self-service collection without a fixed ``collection_name``. Used on
    the tagged remove path; the partitioned write path resolves the collection from the composite key in the
    routed IO manager instead.
    """

    def create_resource(self, context: InitResourceContext) -> MilvusVectorStore:
        bucket = bucket_from_resource_init(context)
        return build_vector_store(get_db_name_from_bucket_name(bucket))
