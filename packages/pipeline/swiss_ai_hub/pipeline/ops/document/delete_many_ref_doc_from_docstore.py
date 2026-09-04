from dagster import OpExecutionContext, op

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_doc_store


@op(code_version="v1")
def delete_many_ref_doc_from_docstore(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
) -> list[RefDocDocument]:
    """Deletes a list of Ref Docs from the docstore of the knowledge database this run targets."""
    doc_store = build_doc_store(get_db_name_from_bucket_name(bucket_from_run_tag(context)))
    for ref_doc in ref_docs:
        context.log.info(f"Deleting ref doc {ref_doc.id_} from docstore")
        doc_store.delete_document(ref_doc.id_, raise_error=True)
    return ref_docs
