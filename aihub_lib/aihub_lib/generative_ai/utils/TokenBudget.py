from enum import Enum
from typing import List

from llama_index.core.schema import NodeWithScore
from llama_index.core.utilities.token_counting import TokenCounter


class BudgetType(str, Enum):
    SUMMARY = "summary"
    CONTENT = "content"
    PARENT = "parent"


class TokenBudget:
    def __init__(
        self,
        max_tokens: int = 50000,
        summary_allocation: float = 0.25,
        content_allocation: float = 0.5,
        parent_allocation: float = 0.25,
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

        self.tokens_used = {k: 0 for k in self.budgets}

        self.selected_nodes = []
        self.selected_ids = set()

        self.token_counter = token_counter or TokenCounter()

    def add_node(self, node: NodeWithScore, budget_type: BudgetType) -> bool:
        if node.node.node_id in self.selected_ids:
            return False

        tokens = self.token_counter.get_string_tokens(node.node.text)
        budget = self.budgets[budget_type]
        used = self.tokens_used[budget_type]

        if used + tokens <= budget:
            self.tokens_used[budget_type] += tokens
            self.selected_nodes.append(node)
            self.selected_ids.add(node.node.node_id)
            return True

        return False

    def add_summary_node(self, node: NodeWithScore) -> bool:
        return self.add_node(node, BudgetType.SUMMARY)

    def add_content_node(self, node: NodeWithScore) -> bool:
        return self.add_node(node, BudgetType.CONTENT)

    def add_parent_node(self, node: NodeWithScore) -> bool:
        return self.add_node(node, BudgetType.PARENT)

    def get_selected_nodes(self) -> List[NodeWithScore]:
        return self.selected_nodes
