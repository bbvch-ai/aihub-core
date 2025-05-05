from typing import List, Optional, Set

from llama_index.core.schema import NodeRelationship, NodeWithScore, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE


def retrieve_parent_summary_nodes(
    content_node: TextNode,
    vector_store: BasePydanticVectorStore,
    max_levels: int = 3,
    visited_ids: Optional[Set[str]] = None,
) -> List[NodeWithScore]:
    if visited_ids is None:
        visited_ids = set()

    parents = []
    current = content_node
    level = 0

    while level < max_levels and NodeRelationship.PARENT in current.relationships:
        parent_info = current.relationships[NodeRelationship.PARENT]

        if not isinstance(parent_info, RelatedNodeInfo):
            break

        parent_id = parent_info.node_id

        if parent_id in visited_ids:
            break

        visited_ids.add(parent_id)

        parent_nodes = vector_store.get_nodes([parent_id])
        if not parent_nodes:
            break

        parent = parent_nodes[0]

        if parent.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
            parents.append(NodeWithScore(node=parent))

        current = parent
        level += 1

    return parents
