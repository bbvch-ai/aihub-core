from typing import List

from dagster import op, Out, Output, MetadataValue, DataVersion
from llama_index.core.schema import TextNode

from pipelines_core.pipelines_core.types.RefDocDocument import RefDocDocument
from pipelines_core.pipelines_core.util.meta_utils import ref_doc_metadata, nodes_metadata_table


@op(code_version="v1", out=Out(io_manager_key="vector_store_io_manager"))
def insert_nodes_into_vector_store(nodes: List[TextNode], ref_doc: RefDocDocument) -> Output[List[TextNode]]:
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
