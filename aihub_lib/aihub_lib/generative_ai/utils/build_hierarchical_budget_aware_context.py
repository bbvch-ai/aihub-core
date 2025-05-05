from typing import List

from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.generative_ai.utils.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from aihub_lib.generative_ai.utils.TokenBudget import TokenBudget
from aihub_lib.persistence.rag.vectors.node_metadata import HEADING_LEVEL


def build_hierarchical_budget_aware_context(
    content_nodes: List[NodeWithScore],
    summary_nodes: List[NodeWithScore],
    vector_store: BasePydanticVectorStore,
    token_budget: TokenBudget,
    max_parent_levels: int = 2,
) -> List[NodeWithScore]:
    """
    Build a hierarchical context with appropriate token allocation.
    """
    sorted_summaries = sorted(
        summary_nodes,
        key=lambda x: (
            x.node.metadata.get(HEADING_LEVEL, 999),  # Primary sort by heading level
            -getattr(x, "score", 0),  # Secondary sort by score (descending)
        ),
    )

    summary_count = 0
    content_count = 0
    parent_count = 0
    selected_content = []

    for summary in sorted_summaries:
        if token_budget.add_summary_node(summary.node):
            summary_count += 1

    sorted_content = sorted(content_nodes, key=lambda x: getattr(x, "score", 0), reverse=True)
    for content in sorted_content:
        if token_budget.add_content_node(content.node):
            selected_content.append(content.node)
            content_count += 1

    visited_parent_ids = set()
    for content_node in selected_content:
        parents = retrieve_parent_summary_nodes(content_node, vector_store, max_levels=max_parent_levels)

        for parent in parents:
            parent_id = parent.node.node_id
            if parent_id not in visited_parent_ids:
                if token_budget.add_parent_node(parent.node):
                    visited_parent_ids.add(parent_id)
                    parent_count += 1

    return token_budget.get_selected_nodes()
