from dagster import ResourceParam, op
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE
from swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusPartitionManager import get_partition_name_for_namespace

from swiss_ai_hub.pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def delete_nodes_for_ref_doc(
    vector_store: ResourceParam[BasePydanticVectorStore],
    ref_doc: RefDocDocument,
) -> RefDocDocument:
    namespace = ref_doc.metadata.get(NAMESPACE, "")
    partition_name = get_partition_name_for_namespace(namespace)
    vector_store.delete(ref_doc.id_, partition_name=partition_name)

    return ref_doc
