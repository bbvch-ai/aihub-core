from dagster import DataVersion, MetadataValue, Out, Output, op
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.meta_utils import nodes_metadata_table, ref_doc_metadata


@op(code_version="v1", out=Out(io_manager_key="vector_store_io_manager"))
def insert_nodes_into_vector_store(nodes: list[TextNode], ref_doc: RefDocDocument) -> Output[list[TextNode]]:
    """Inserts a list of nodes into the vector store by having the appropriate
    IO manager set as the output IO Manager"""
    return Output(
        nodes,
        metadata={
            **ref_doc_metadata(ref_doc),
            "Number of Nodes": MetadataValue.int(len(nodes)),
            "Nodes Table": nodes_metadata_table(nodes),
        },
        data_version=DataVersion(f"{ref_doc.updated}-{ref_doc.hash}"),
    )
