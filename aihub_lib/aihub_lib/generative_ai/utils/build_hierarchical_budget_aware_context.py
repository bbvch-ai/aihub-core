from typing import List

from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.generative_ai.utils.retrieve_parent_summary_nodes import retrieve_parent_summary_nodes
from aihub_lib.generative_ai.utils.TokenBudget import TokenBudget


def build_hierarchical_budget_aware_context(
    content_nodes: List[NodeWithScore],
    summary_nodes: List[NodeWithScore],
    vector_store: BasePydanticVectorStore,
    token_budget: TokenBudget,
    max_parent_levels: int = 2,
) -> List[NodeWithScore]:
    sorted_summaries = sorted(summary_nodes, key=lambda x: getattr(x, "score", 0) or 0, reverse=True)
    for summary in sorted_summaries:
        node_added = token_budget.add_summary_node(summary)
        if not node_added:
            break

    sorted_content = sorted(content_nodes, key=lambda x: getattr(x, "score", 0) or 0, reverse=True)
    selected_content = []
    for content in sorted_content:
        node_added = token_budget.add_content_node(content)
        if node_added:
            selected_content.append(content)
        else:
            break

    visited_parent_ids = set()
    for content_node in selected_content:
        parents = retrieve_parent_summary_nodes(content_node, vector_store, max_levels=max_parent_levels)

        for parent in parents:
            parent_id = parent.node.node_id
            if parent_id not in visited_parent_ids:
                if token_budget.add_parent_node(parent):
                    visited_parent_ids.add(parent_id)

    return token_budget.get_selected_nodes()
