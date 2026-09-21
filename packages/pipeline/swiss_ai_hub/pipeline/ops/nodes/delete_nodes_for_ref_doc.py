from dagster import OpExecutionContext, op
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import get_partition_name_for_namespace

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store


@op(code_version="v1")
def delete_nodes_for_ref_doc(context: OpExecutionContext, ref_doc: RefDocDocument) -> RefDocDocument:
    """Route-per-run variant of ``delete_nodes_for_ref_doc``.

    Auto-materialized ``nodes`` runs carry only the composite partition key, so the target collection is
    resolved from the key's bucket rather than from a fixed ``vector_store`` resource. Deleting the ref doc's
    existing nodes before re-chunking keeps re-observes consistent when a document yields fewer nodes.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    vector_store = build_vector_store(get_db_name_from_bucket_name(bucket))

    namespace = ref_doc.metadata.get(NAMESPACE, "")
    partition_name = get_partition_name_for_namespace(namespace)
    vector_store.delete(ref_doc.id_, partition_name=partition_name)

    return ref_doc
