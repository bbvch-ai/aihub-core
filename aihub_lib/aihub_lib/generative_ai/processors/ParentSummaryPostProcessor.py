from typing import Annotated, Dict, List, Optional, Set

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeRelationship, NodeWithScore, QueryBundle, RelatedNodeInfo
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE


class ParentSummaryPostProcessor(BaseNodePostprocessor):
    """
    Post-processor to fetch parent summary nodes based on hierarchical relationships.
    """

    vectorstore: BasePydanticVectorStore
    max_levels: Annotated[int, "Maximum levels to traverse for parent summaries."] = 3

    @classmethod
    def class_name(cls) -> str:
        return "ParentSummaryPostProcessor"

    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        all_nodes: Dict[str, NodeWithScore] = {}

        for node in nodes:
            all_nodes[node.node.node_id] = node

        visited_ids = set(all_nodes.keys())

        for node in nodes:
            parent_summaries = self._retrieve_nodes(node, visited_ids=visited_ids)

            for parent in parent_summaries:
                if parent.node.node_id not in all_nodes:
                    all_nodes[parent.node.node_id] = parent
                    visited_ids.add(parent.node.node_id)

        return list(all_nodes.values())

    def _retrieve_nodes(
        self,
        content_node: NodeWithScore,
        visited_ids: Optional[Set[str]] = None,
    ) -> List[NodeWithScore]:
        if visited_ids is None:
            visited_ids = set()

        parents = []
        current = content_node
        level = 0

        while level < self.max_levels and NodeRelationship.PARENT in current.node.relationships:
            parent_info = current.node.relationships[NodeRelationship.PARENT]
            if not isinstance(parent_info, RelatedNodeInfo):
                break

            parent_id = parent_info.node_id
            if parent_id in visited_ids:
                break

            visited_ids.add(parent_id)
            parent_nodes = self.vector_store.get_nodes([parent_id])
            if not parent_nodes:
                break

            parent_node = parent_nodes[0]
            parent = NodeWithScore(node=parent_node, score=0)

            if parent.node.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
                parents.append(parent)

            current = parent
            level += 1

        return parents
