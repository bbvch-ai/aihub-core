from typing import List

from dagster import op, ResourceParam, OpExecutionContext
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from pipelines_core.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def delete_many_nodes_from_vector_store(
    context: OpExecutionContext,
    vector_store: ResourceParam[BasePydanticVectorStore],
    ref_docs: List[RefDocDocument],
) -> List[RefDocDocument]:
    """Deletes all nodes related to any of the given ref docs from the vector store."""
    for ref_doc in ref_docs:
        context.log.info(f"Deleting nodes for ref doc {ref_doc.id_} from vector store")
        vector_store.delete(ref_doc.id_)
    return ref_docs
