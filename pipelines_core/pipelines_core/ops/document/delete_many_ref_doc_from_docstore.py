from typing import List

from dagster import OpExecutionContext, ResourceParam, op
from llama_index.core.storage.docstore.keyval_docstore import KVDocumentStore

from pipelines_core.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def delete_many_ref_doc_from_docstore(
    context: OpExecutionContext,
    doc_store: ResourceParam[KVDocumentStore],
    ref_docs: List[RefDocDocument],
) -> List[RefDocDocument]:
    """Deletes a list of Ref Docs from the docstore."""
    for ref_doc in ref_docs:
        context.log.info(f"Deleting ref doc {ref_doc.id_} from docstore")
        doc_store.delete_document(ref_doc.id_, raise_error=True)
    return ref_docs
