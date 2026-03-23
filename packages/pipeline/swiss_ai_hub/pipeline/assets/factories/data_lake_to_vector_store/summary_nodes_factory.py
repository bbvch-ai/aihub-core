from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.ops.nodes.embed_nodes import embed_nodes
from swiss_ai_hub.pipeline.ops.nodes.ensure_node_default_metadata import ensure_node_default_metadata
from swiss_ai_hub.pipeline.ops.nodes.extend_nodes_with_summary_nodes_using_recursive_summary_parser import (
    extend_nodes_with_summary_nodes_using_recursive_summary_parser,
)
from swiss_ai_hub.pipeline.ops.nodes.insert_nodes_into_vector_store import insert_nodes_into_vector_store
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def summary_nodes_factory(
    key: AssetKey, document_key: str | AssetKey, nodes_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """
    Creates a graph asset that generates summary nodes for a Ref Doc based on input nodes.
    This asset orchestrates an advanced workflow where the provided nodes are extended with summary nodes
    using a recursive summary parser. The extended nodes are then embedded and inserted into the Vector Store
    while associating them with the corresponding document.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"nodes": AssetIn(key=nodes_key), "document": AssetIn(key=document_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Generates summary nodes for a reference document by extending input nodes with summary nodes, "
        "embedding them, and inserting them into a vector store.",
    )
    def summary_nodes(nodes: list[TextNode], document: RefDocDocument) -> Output[list[TextNode]]:
        return insert_nodes_into_vector_store(
            embed_nodes(
                ensure_node_default_metadata(extend_nodes_with_summary_nodes_using_recursive_summary_parser(nodes)),
            ),
            document,
        )

    return summary_nodes
