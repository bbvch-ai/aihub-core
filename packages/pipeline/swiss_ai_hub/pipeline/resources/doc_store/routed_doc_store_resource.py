from dagster import ConfigurableResource, InitResourceContext

from swiss_ai_hub.pipeline.resources.doc_store.doc_store_resource import DocStoreResource
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_resource_init


class RoutedDocStoreResource(ConfigurableResource[DocStoreResource]):
    """Per-run ``DocStoreResource`` for the RAG pipeline, scoped to the run's bucket.

    Resolves the store name from the ``aihub/bucket`` run tag and yields a plain ``DocStoreResource`` so
    ops that only read ``document_store_name`` (e.g. ``fetch_ref_docs_to_remove``) work unchanged.
    """

    def create_resource(self, context: InitResourceContext) -> DocStoreResource:
        bucket = bucket_from_resource_init(context)
        return DocStoreResource(document_store_name=get_db_name_from_bucket_name(bucket))
