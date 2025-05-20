import unittest
from unittest.mock import MagicMock

from llama_index.core.schema import NodeWithScore, TextNode

from aihub_lib.generative_ai.utils.TokenBudget import BudgetType, TokenBudget


class TestTokenBudget(unittest.TestCase):
    """Simple direct tests for TokenBudget without using pytest-bdd."""

    def setUp(self):
        """Create a token budget and test nodes for each test."""
        # Create a mock token counter
        self.token_counter = MagicMock()

        # Create a budget with standard allocations
        self.budget = TokenBudget(
            max_tokens=1000,
            summary_allocation=0.25,  # 250 tokens
            content_allocation=0.65,  # 650 tokens
            parent_allocation=0.10,  # 100 tokens
            token_counter=self.token_counter,
        )

        # Configure the token counter mock to return fixed values
        self.token_counter.get_string_tokens.side_effect = self._token_count_side_effect

        # Create test nodes
        self.create_test_nodes()

    def _token_count_side_effect(self, text):
        """Return token count based on the text content."""
        if "30 tokens" in text:
            return 30
        elif "40 tokens" in text:
            return 40
        elif "50 tokens" in text:
            return 50
        elif "200 tokens" in text:
            return 200
        elif "25 tokens" in text:
            return 25
        elif "300 tokens" in text:
            return 300
        elif "large" in text.lower():
            return 1000
        else:
            return len(text) // 5  # Fallback estimation

    def create_test_nodes(self):
        """Create various test nodes with known token counts."""
        # Summary nodes
        self.summary_node1 = NodeWithScore(
            node=TextNode(text="This is a summary node with 30 tokens", id_="summary1"), score=1.0
        )

        self.summary_node2 = NodeWithScore(
            node=TextNode(text="This is another summary node with 40 tokens", id_="summary2"), score=1.0
        )

        # Content nodes
        self.content_node1 = NodeWithScore(
            node=TextNode(text="This is a content node with 50 tokens", id_="content1"), score=1.0
        )

        self.content_node2 = NodeWithScore(
            node=TextNode(text="This is a larger content node with 200 tokens", id_="content2"), score=1.0
        )

        # Parent nodes
        self.parent_node1 = NodeWithScore(
            node=TextNode(text="This is a parent node with 25 tokens", id_="parent1"), score=1.0
        )

        self.parent_node2 = NodeWithScore(
            node=TextNode(text="This is another parent node with 25 tokens", id_="parent2"), score=1.0
        )

        # Large nodes that should exceed the budgets
        self.large_summary_node = NodeWithScore(
            node=TextNode(text="This is a large summary node with 300 tokens", id_="large_summary"), score=1.0
        )

        self.large_content_node = NodeWithScore(
            node=TextNode(text="This is a large content node", id_="large_content"), score=1.0
        )

        self.large_parent_node = NodeWithScore(
            node=TextNode(text="This is a large parent node", id_="large_parent"), score=1.0
        )

    def test_budget_initialization(self):
        """Test that the budget is initialized with correct allocations."""
        self.assertEqual(self.budget.budgets[BudgetType.SUMMARY], 250)
        self.assertEqual(self.budget.budgets[BudgetType.CONTENT], 650)
        self.assertEqual(self.budget.budgets[BudgetType.PARENT], 100)

        self.assertEqual(self.budget.tokens_used[BudgetType.SUMMARY], 0)
        self.assertEqual(self.budget.tokens_used[BudgetType.CONTENT], 0)
        self.assertEqual(self.budget.tokens_used[BudgetType.PARENT], 0)

    def test_add_nodes_within_budget(self):
        """Test adding nodes that fit within their respective budgets."""
        # Add one node of each type
        self.assertTrue(self.budget.add_summary_node(self.summary_node1))
        self.assertTrue(self.budget.add_content_node(self.content_node1))
        self.assertTrue(self.budget.add_parent_node(self.parent_node1))

        # Check tokens used
        self.assertEqual(self.budget.tokens_used[BudgetType.SUMMARY], 30)
        self.assertEqual(self.budget.tokens_used[BudgetType.CONTENT], 50)
        self.assertEqual(self.budget.tokens_used[BudgetType.PARENT], 25)

        # Check selected nodes
        self.assertEqual(len(self.budget.selected_nodes), 3)
        self.assertEqual(len(self.budget.selected_ids), 3)

        selected_ids = {node.node.id_ for node in self.budget.selected_nodes}
        self.assertEqual(selected_ids, {"summary1", "content1", "parent1"})

    def test_exceeding_summary_budget(self):
        """Test that nodes are rejected when they exceed the summary budget."""
        # Add summary nodes up to near the limit
        self.assertTrue(self.budget.add_summary_node(self.summary_node1))  # 30 tokens
        self.assertTrue(self.budget.add_summary_node(self.summary_node2))  # 40 tokens

        # This should use 30 + 40 = 70 tokens out of 250
        self.assertEqual(self.budget.tokens_used[BudgetType.SUMMARY], 70)

        # Try to add a large node that would exceed the budget
        # The large_summary_node has 300 tokens, which exceeds remaining budget (180)
        self.assertFalse(self.budget.add_summary_node(self.large_summary_node))

        # Check tokens used (should not have increased)
        self.assertEqual(self.budget.tokens_used[BudgetType.SUMMARY], 70)

        # Check selected nodes (should only have the first two)
        self.assertEqual(len(self.budget.selected_nodes), 2)
        selected_ids = {node.node.id_ for node in self.budget.selected_nodes}
        self.assertEqual(selected_ids, {"summary1", "summary2"})

    def test_exceeding_content_budget(self):
        """Test that nodes are rejected when they exceed the content budget."""
        # Add content nodes up to near the limit
        self.assertTrue(self.budget.add_content_node(self.content_node1))  # 50 tokens
        self.assertTrue(self.budget.add_content_node(self.content_node2))  # 200 tokens

        # This should use 50 + 200 = 250 tokens out of 650
        self.assertEqual(self.budget.tokens_used[BudgetType.CONTENT], 250)

        # Try to add a large node that would exceed the budget
        # The large_content_node has 1000 tokens, which exceeds remaining budget (400)
        self.assertFalse(self.budget.add_content_node(self.large_content_node))

        # Check tokens used (should not have increased)
        self.assertEqual(self.budget.tokens_used[BudgetType.CONTENT], 250)

        # Check selected nodes (should only have the first two)
        self.assertEqual(len(self.budget.selected_nodes), 2)
        selected_ids = {node.node.id_ for node in self.budget.selected_nodes}
        self.assertEqual(selected_ids, {"content1", "content2"})

    def test_exceeding_parent_budget(self):
        """Test that nodes are rejected when they exceed the parent budget."""
        # Add parent nodes up to near the limit
        self.assertTrue(self.budget.add_parent_node(self.parent_node1))  # 25 tokens
        self.assertTrue(self.budget.add_parent_node(self.parent_node2))  # 25 tokens

        # This should use 25 + 25 = 50 tokens out of 100
        self.assertEqual(self.budget.tokens_used[BudgetType.PARENT], 50)

        # Try to add a large node that would exceed the budget
        # The large_parent_node has 1000 tokens, which exceeds remaining budget (50)
        self.assertFalse(self.budget.add_parent_node(self.large_parent_node))

        # Check tokens used (should not have increased)
        self.assertEqual(self.budget.tokens_used[BudgetType.PARENT], 50)

        # Check selected nodes (should only have the first two)
        self.assertEqual(len(self.budget.selected_nodes), 2)
        selected_ids = {node.node.id_ for node in self.budget.selected_nodes}
        self.assertEqual(selected_ids, {"parent1", "parent2"})

    def test_duplicate_node_rejection(self):
        """Test that duplicate nodes are rejected."""
        # Add a node first as summary
        self.assertTrue(self.budget.add_summary_node(self.summary_node1))

        # Try to add the same node as content (should be rejected)
        self.assertFalse(self.budget.add_content_node(self.summary_node1))

        # Check tokens used
        self.assertEqual(self.budget.tokens_used[BudgetType.SUMMARY], 30)
        self.assertEqual(self.budget.tokens_used[BudgetType.CONTENT], 0)

        # Check selected nodes
        self.assertEqual(len(self.budget.selected_nodes), 1)
        self.assertEqual(self.budget.selected_nodes[0].node.id_, "summary1")

    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        # Add nodes of each type
        self.budget.add_summary_node(self.summary_node1)  # 30 tokens
        self.budget.add_content_node(self.content_node1)  # 50 tokens
        self.budget.add_parent_node(self.parent_node1)  # 25 tokens

        # Get usage stats
        stats = self.budget.get_usage_stats()

        # Check the stats
        self.assertEqual(stats["summary_tokens"], 30)
        self.assertEqual(stats["summary_budget"], 250)
        self.assertEqual(stats["content_tokens"], 50)
        self.assertEqual(stats["content_budget"], 650)
        self.assertEqual(stats["parent_tokens"], 25)
        self.assertEqual(stats["parent_budget"], 100)
        self.assertEqual(stats["total_tokens"], 105)
        self.assertEqual(stats["max_tokens"], 1000)

    def test_get_budget_utilization(self):
        """Test getting budget utilization percentages."""
        # Add nodes of each type
        self.budget.add_summary_node(self.summary_node1)  # 30/250 = 0.12
        self.budget.add_content_node(self.content_node1)  # 50/650 = ~0.077
        self.budget.add_parent_node(self.parent_node1)  # 25/100 = 0.25

        # Get utilization
        utilization = self.budget.get_budget_utilization()

        # Check utilization with tolerance for floating point
        self.assertAlmostEqual(utilization[BudgetType.SUMMARY], 0.12, places=2)
        self.assertAlmostEqual(utilization[BudgetType.CONTENT], 0.077, places=3)
        self.assertAlmostEqual(utilization[BudgetType.PARENT], 0.25, places=2)

    def test_custom_allocation(self):
        """Test creating a budget with custom allocations."""
        custom_budget = TokenBudget(
            max_tokens=2000,
            summary_allocation=0.5,  # 1000 tokens
            content_allocation=0.3,  # 600 tokens
            parent_allocation=0.2,  # 400 tokens
            token_counter=self.token_counter,
        )

        # Check the budgets
        self.assertEqual(custom_budget.budgets[BudgetType.SUMMARY], 1000)
        self.assertEqual(custom_budget.budgets[BudgetType.CONTENT], 600)
        self.assertEqual(custom_budget.budgets[BudgetType.PARENT], 400)


if __name__ == "__main__":
    unittest.main()
