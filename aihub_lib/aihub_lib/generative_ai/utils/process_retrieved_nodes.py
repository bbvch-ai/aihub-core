from aihub_lib.generative_ai.utils.build_hierarchical_budget_aware_context import (
    build_hierarchical_budget_aware_context,
)
from aihub_lib.generative_ai.utils.TokenBudget import TokenBudget
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE


def process_retrieved_nodes(
    nodes,
    vector_store,
    max_tokens=100000,
    max_parent_levels=2,
    summary_allocation=0.25,
    content_allocation=0.50,
    parent_allocation=0.25,
):
    content_nodes = []
    summary_nodes = []

    for node in nodes:
        if node.node.metadata.get(TYPE) == NODE_TYPE_SUMMARY:
            summary_nodes.append(node)
        else:
            content_nodes.append(node)

    token_budget = TokenBudget(
        max_tokens=max_tokens,
        summary_allocation=summary_allocation,
        content_allocation=content_allocation,
        parent_allocation=parent_allocation,
    )

    enhanced_nodes = build_hierarchical_budget_aware_context(
        content_nodes=content_nodes,
        summary_nodes=summary_nodes,
        vector_store=vector_store,
        token_budget=token_budget,
        max_parent_levels=max_parent_levels,
    )

    return enhanced_nodes
