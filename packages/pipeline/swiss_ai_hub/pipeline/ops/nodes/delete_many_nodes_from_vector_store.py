from dagster import OpExecutionContext, op

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store


@op(code_version="v2")
def delete_many_nodes_from_vector_store(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
) -> list[RefDocDocument]:
    """Deletes all nodes related to any of the given ref docs from this run's collection.

    Grouping by namespace lets each delete load only that namespace's partition instead of the whole
    collection, which does not fit in memory once it is partitioned.
    """
    vector_store = build_vector_store(get_db_name_from_bucket_name(bucket_from_run_tag(context)))

    ref_doc_ids_by_namespace: dict[str, list[str]] = {}
    for ref_doc in ref_docs:
        context.log.info(f"Deleting nodes for ref doc {ref_doc.id_} in namespace '{ref_doc.namespace}'")
        ref_doc_ids_by_namespace.setdefault(ref_doc.namespace, []).append(ref_doc.id_)

    for namespace, ref_doc_ids in ref_doc_ids_by_namespace.items():
        deleted = vector_store.delete_documents(ref_doc_ids, [namespace])
        context.log.info(f"Deleted {deleted} nodes of {len(ref_doc_ids)} ref docs in namespace '{namespace}'")
    return ref_docs
