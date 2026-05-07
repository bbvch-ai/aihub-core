from typing import Annotated, Any

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeRelationship, NodeWithScore, QueryBundle, RelatedNodeInfo
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, NODE_TYPE_SUMMARY, TYPE


class ParentSummaryPostProcessor(BaseNodePostprocessor):
    """
    Post-processor to fetch parent summary nodes based on hierarchical relationships.
    """

    vectorstore: Annotated[BasePydanticVectorStore, "Vector store to retrieve parent nodes."]
    max_levels: Annotated[int, "Maximum levels to traverse for parent summaries."] = 3

    @classmethod
    def class_name(cls) -> str:
        return "ParentSummaryPostProcessor"

    def _postprocess_nodes(
        self, nodes: list[NodeWithScore], query_bundle: QueryBundle | None = None
    ) -> list[NodeWithScore]:
        all_nodes: dict[str, NodeWithScore] = {n.node.node_id: n for n in nodes}

        for node in nodes:
            visited_ids = set(all_nodes.keys())

            parent_summaries = self._retrieve_parents_for_node(node, visited_ids)

            for parent in parent_summaries:
                all_nodes[parent.node.node_id] = parent

        return list(all_nodes.values())

    def _retrieve_parents_for_node(
        self,
        content_node: NodeWithScore,
        visited_ids: set[str],
    ) -> list[NodeWithScore]:
        parents: list[NodeWithScore] = []
        current_node = content_node
        level = 0

        # Scope parent fetches to the source node's namespace so partition-aware stores
        # avoid loading the whole collection. Empty-string namespace (DEFAULT_METADATA
        # in node_metadata.py) is treated as unscoped.
        namespace: str | None = content_node.node.metadata.get(NAMESPACE)
        scope_kwargs: dict[str, Any] = {"namespaces": [namespace]} if namespace else {}

        while level < self.max_levels and NodeRelationship.PARENT in current_node.node.relationships:
            parent_info = current_node.node.relationships[NodeRelationship.PARENT]
            if not isinstance(parent_info, RelatedNodeInfo):
                break

            parent_id = parent_info.node_id
            if parent_id in visited_ids:
                break

            visited_ids.add(parent_id)
            parent_nodes = self.vectorstore.get_nodes([parent_id], **scope_kwargs)
            if not parent_nodes:
                break

            parent_node = NodeWithScore(node=parent_nodes[0], score=0.0)
            if parent_node.node.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
                parents.append(parent_node)

            current_node = parent_node
            level += 1

        return parents
