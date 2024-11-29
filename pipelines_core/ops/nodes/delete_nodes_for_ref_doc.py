from dagster import op, ResourceParam
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from pipelines_core.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def delete_nodes_for_ref_doc(
    vector_store: ResourceParam[BasePydanticVectorStore],
    ref_doc: RefDocDocument,
) -> RefDocDocument:
    """Deletes nodes related to a given ref doc from the vector store."""
    vector_store.delete(ref_doc.id_)
    return ref_doc
