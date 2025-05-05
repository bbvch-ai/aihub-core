from enum import Enum
from typing import Dict, List, Literal

from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.utilities.token_counting import TokenCounter


class BudgetType(str, Enum):
    SUMMARY = "summary"
    CONTENT = "content"
    PARENT = "parent"


class TokenBudget:
    """Token budget manager for hierarchical context allocation."""

    def __init__(
        self,
        max_tokens: int = 4000,
        summary_allocation: float = 0.25,
        content_allocation: float = 0.65,
        parent_allocation: float = 0.10,
        token_counter=None,
    ):
        if not (0.99 < summary_allocation + content_allocation + parent_allocation < 1.01):
            raise ValueError("Budget allocations must sum to approximately 1.0")

        self.max_tokens = max_tokens
        self.budgets = {
            BudgetType.SUMMARY: int(max_tokens * summary_allocation),
            BudgetType.CONTENT: int(max_tokens * content_allocation),
            BudgetType.PARENT: int(max_tokens * parent_allocation),
        }

        self.tokens_used = {BudgetType.SUMMARY: 0, BudgetType.CONTENT: 0, BudgetType.PARENT: 0}

        self.selected_nodes = []
        self.selected_ids = set()

        self.token_counter = token_counter or TokenCounter()

    def estimate_tokens(self, text: str) -> int:
        return self.token_counter.estimate_tokens(text)

    def add_node(
        self, node: TextNode, budget_type: Literal[BudgetType.SUMMARY, BudgetType.CONTENT, BudgetType.PARENT]
    ) -> bool:
        """
        Add a node to the context if it fits in the budget.
        """
        if node.node_id in self.selected_ids:
            return False

        tokens = self.estimate_tokens(node.text)
        budget = self.budgets[budget_type]
        used = self.tokens_used[budget_type]

        if used + tokens <= budget:
            self.tokens_used[budget_type] += tokens
            self.selected_nodes.append(NodeWithScore(node=node))
            self.selected_ids.add(node.node_id)
            return True

        return False

    def add_summary_node(self, node: TextNode) -> bool:
        return self.add_node(node, BudgetType.SUMMARY)

    def add_content_node(self, node: TextNode) -> bool:
        return self.add_node(node, BudgetType.CONTENT)

    def add_parent_node(self, node: TextNode) -> bool:
        return self.add_node(node, BudgetType.PARENT)

    def get_usage_stats(self) -> Dict[str, int]:
        return {
            "summary_tokens": self.tokens_used[BudgetType.SUMMARY],
            "summary_budget": self.budgets[BudgetType.SUMMARY],
            "content_tokens": self.tokens_used[BudgetType.CONTENT],
            "content_budget": self.budgets[BudgetType.CONTENT],
            "parent_tokens": self.tokens_used[BudgetType.PARENT],
            "parent_budget": self.budgets[BudgetType.PARENT],
            "total_tokens": self.get_total_used_tokens(),
            "max_tokens": self.max_tokens,
        }

    def get_total_used_tokens(self) -> int:
        return sum(self.tokens_used.values())

    def get_remaining_tokens(self) -> int:
        return self.max_tokens - self.get_total_used_tokens()

    def get_budget_utilization(self) -> Dict[str, float]:
        return {budget_type: self.tokens_used[budget_type] / self.budgets[budget_type] for budget_type in self.budgets}

    def get_selected_nodes(self) -> List[NodeWithScore]:
        return self.selected_nodes
