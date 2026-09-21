from dagster import OpExecutionContext, op

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store


@op(code_version="v1")
def delete_many_nodes_from_vector_store(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
) -> list[RefDocDocument]:
    """Deletes all nodes related to any of the given ref docs from this run's collection."""
    vector_store = build_vector_store(get_db_name_from_bucket_name(bucket_from_run_tag(context)))
    for ref_doc in ref_docs:
        context.log.info(f"Deleting nodes for ref doc {ref_doc.id_} from vector store")
        vector_store.delete(ref_doc.id_)
    return ref_docs
