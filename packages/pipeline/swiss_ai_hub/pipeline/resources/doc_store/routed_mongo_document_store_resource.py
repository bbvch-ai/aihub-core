from dagster import ConfigurableResource, InitResourceContext
from llama_index.storage.docstore.mongodb import MongoDocumentStore

from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_resource_init
from swiss_ai_hub.pipeline.util.store_builders import build_doc_store


class RoutedMongoDocumentStoreResource(ConfigurableResource[MongoDocumentStore]):
    """Per-run Mongo document store for the RAG pipeline, scoped to the run's bucket.

    Resolves the store name from the ``aihub/bucket`` run tag so the RAG pipeline can clean up
    documents from any self-service database without a fixed ``document_store_name``. Used on the tagged
    remove path; the partitioned write path resolves the store from the composite key in the routed IO
    manager instead.
    """

    def create_resource(self, context: InitResourceContext) -> MongoDocumentStore:
        bucket = bucket_from_resource_init(context)
        return build_doc_store(get_db_name_from_bucket_name(bucket))
