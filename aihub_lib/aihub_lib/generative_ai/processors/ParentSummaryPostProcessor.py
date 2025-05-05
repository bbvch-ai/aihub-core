from typing import Dict, List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.generative_ai.utils.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE


class ParentSummaryPostProcessor(BaseNodePostprocessor):
    """
    Post-processor to fetch parent summary nodes based on hierarchical relationships.
    """

    vectorstore: BasePydanticVectorStore
    max_levels: int = 3

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
            if node.node.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
                continue

            parent_summaries = retrieve_parent_summary_nodes(
                node.node, self.vectorstore, self.max_levels, visited_ids.copy()
            )

            for parent in parent_summaries:
                if parent.node.node_id not in all_nodes:
                    all_nodes[parent.node.node_id] = parent
                    visited_ids.add(parent.node.node_id)

        return list(all_nodes.values())
