from typing import List

from dagster import graph_asset, AutomationCondition, Output, DynamicPartitionsDefinition, AssetIn, AssetKey
from llama_index.core.schema import TextNode

from pipelines_core.pipelines_core.ops.nodes.chunk_ref_doc_into_nodes_using_md_structural_node_parser import (
    chunk_ref_doc_into_nodes_using_md_structural_node_parser,
)
from pipelines_core.pipelines_core.ops.nodes.delete_nodes_for_ref_doc import delete_nodes_for_ref_doc
from pipelines_core.pipelines_core.ops.nodes.embed_nodes import embed_nodes

from pipelines_core.pipelines_core.ops.nodes.insert_nodes_into_vector_store import insert_nodes_into_vector_store
from pipelines_core.pipelines_core.types.RefDocDocument import RefDocDocument
from pipelines_core.pipelines_core.util.key_utils import group_name_from_asset_key


def nodes_factory(key: AssetKey, document_key: str, partitions: DynamicPartitionsDefinition) -> graph_asset:
    """Creates a nodes asset that represents nodes from a chunked up Ref Doc in the Vector Store.
    This asset takes a Ref Doc as input, splits it into nodes, and saves the nodes in the Vector Store as
    well as providing the nodes as an output for downstream assets.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"document": AssetIn(key=document_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Chunks a RefDoc into Nodes and inserts them into the Vector Store",
    )
    def nodes(
        document: RefDocDocument,
    ) -> Output[List[TextNode]]:
        return insert_nodes_into_vector_store(
            embed_nodes(chunk_ref_doc_into_nodes_using_md_structural_node_parser(delete_nodes_for_ref_doc(document))),
            document,
        )

    return nodes
