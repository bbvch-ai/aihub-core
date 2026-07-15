from dagster import AssetIn, AssetKey, AutomationCondition, DynamicPartitionsDefinition, Output, graph_asset
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.ops.nodes.embed_nodes import embed_nodes
from swiss_ai_hub.pipeline.ops.nodes.ensure_node_default_metadata import ensure_node_default_metadata
from swiss_ai_hub.pipeline.ops.nodes.insert_nodes_into_vector_store import insert_nodes_into_vector_store
from swiss_ai_hub.pipeline.ops.nodes.routed_chunk_ref_doc_into_nodes import routed_chunk_ref_doc_into_nodes
from swiss_ai_hub.pipeline.ops.nodes.routed_delete_nodes_for_ref_doc import routed_delete_nodes_for_ref_doc
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def routed_nodes_factory(
    key: AssetKey, document_key: str | AssetKey, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Route-per-run variant of ``nodes_factory``.

    Identical chunk → embed → insert chain, but the delete and chunk ops are the routed variants that resolve
    their store from the composite partition key (the per-run write path carries no bucket tag). Embedding,
    metadata, and insertion are reused unchanged — ``insert_nodes_into_vector_store`` persists via the
    ``vector_store_io_manager`` key, which is wired to the routed vector-store IO manager.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"document": AssetIn(key=document_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Chunks a RefDoc into Nodes and inserts them into the routed Vector Store",
    )
    def nodes(document: RefDocDocument) -> Output[list[TextNode]]:
        return insert_nodes_into_vector_store(
            embed_nodes(
                ensure_node_default_metadata(routed_chunk_ref_doc_into_nodes(routed_delete_nodes_for_ref_doc(document)))
            ),
            document,
        )

    return nodes
