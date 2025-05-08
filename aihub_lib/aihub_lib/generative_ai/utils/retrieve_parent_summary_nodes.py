from typing import List, Optional, Set

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, NodeWithScore
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE


def retrieve_parent_summary_nodes(
    content_node: NodeWithScore,
    vector_store: BasePydanticVectorStore,
    max_levels: int = 3,
    visited_ids: Optional[Set[str]] = None,
) -> List[NodeWithScore]:
    print("Retrieving parent summary nodes")
    if visited_ids is None:
        visited_ids = set()

    parents = []
    current = content_node
    level = 0

    while level < max_levels and NodeRelationship.PARENT in current.node.relationships:
        print("Retrieving parent summary node for level:", level)
        parent_info = current.node.relationships[NodeRelationship.PARENT]
        print("Parent info:", parent_info)
        if not isinstance(parent_info, RelatedNodeInfo):
            break

        parent_id = parent_info.node_id
        print("Parent ID:", parent_id)
        if parent_id in visited_ids:
            break

        visited_ids.add(parent_id)
        parent_nodes = vector_store.get_nodes([parent_id])
        if not parent_nodes:
            print("No parent nodes found for ID:", parent_id)
            break

        parent_node = parent_nodes[0]
        parent = NodeWithScore(node=parent_node, score=0)

        if parent.node.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
            print("Adding parent summary node:", parent.node_id)
            parents.append(parent)

        current = parent
        level += 1

    return parents
