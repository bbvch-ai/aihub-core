from dagster import OpExecutionContext, ResourceParam, op
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
def delete_many_nodes_from_vector_store(
    context: OpExecutionContext,
    vector_store: ResourceParam[BasePydanticVectorStore],
    ref_docs: list[RefDocDocument],
) -> list[RefDocDocument]:
    """Deletes all nodes related to any of the given ref docs from the vector store."""
    for ref_doc in ref_docs:
        context.log.info(f"Deleting nodes for ref doc {ref_doc.id_} from vector store")
        vector_store.delete(ref_doc.id_)
    return ref_docs
