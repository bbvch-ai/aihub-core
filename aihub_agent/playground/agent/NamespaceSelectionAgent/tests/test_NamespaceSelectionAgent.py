"""Tests for NamespaceSelectionAgent.

These tests verify the NamespaceSelectionAgent components work correctly.
Note: Full integration tests require Redis, NATS, and MongoDB infrastructure.
"""

from unittest.mock import MagicMock

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.agents.NamespaceSelectionAgent.configs import NamespaceSelectionAgentConfig
from aihub_agent.agents.NamespaceSelectionAgent.events import (
    DetermineNamespacesEvent,
    FollowUpQuestionHitl,
    NamespaceApprovalHitl,
)
from aihub_agent.agents.NamespaceSelectionAgent.llm.NamespaceDecision import NamespaceDecision
from aihub_agent.agents.NamespaceSelectionAgent.utils import (
    format_approval_question,
    format_available_namespaces,
    format_conversation_history,
)


class TestNamespaceDecision:
    """Tests for NamespaceDecision model."""

    def test_decision_with_enough_info(self):
        """Test creating a decision when enough info is available."""
        decision = NamespaceDecision(
            has_enough_information=True,
            selected_namespaces={"bucket1": "ns1"},
            reasoning="User clearly mentioned topic X",
        )
        assert decision.has_enough_information is True
        assert decision.selected_namespaces == {"bucket1": "ns1"}
        assert decision.follow_up_question is None

    def test_decision_needs_more_info(self):
        """Test creating a decision when more info is needed."""
        decision = NamespaceDecision(
            has_enough_information=False,
            follow_up_question="What topic are you interested in?",
            reasoning="User query is too vague",
        )
        assert decision.has_enough_information is False
        assert decision.selected_namespaces is None
        assert decision.follow_up_question == "What topic are you interested in?"


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_available_namespaces(self):
        """Test formatting namespaces for LLM prompt."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3"]}
        result = format_available_namespaces(available)
        assert "bucket1" in result
        assert "ns1" in result
        assert "ns2" in result
        assert "bucket2" in result
        assert "ns3" in result

    def test_format_conversation_history(self):
        """Test formatting conversation history for LLM prompt."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = format_conversation_history(history)
        assert "USER: Hello" in result
        assert "ASSISTANT: Hi there" in result

    def test_format_approval_question(self):
        """Test formatting approval question with namespaces."""
        selected = {"bucket1": "ns1", "bucket2": "ns2"}
        template = LocaleString(en="Approve these?\n{namespaces}")
        t = MagicMock()
        t.extract = lambda x: x.en if hasattr(x, "en") else x
        result = format_approval_question(selected, template, t)
        assert "bucket1" in result
        assert "ns1" in result
        assert "bucket2" in result
        assert "ns2" in result


class TestEvents:
    """Tests for event definitions."""

    def test_determine_namespaces_event_creation(self):
        """Test creating a DetermineNamespacesEvent."""
        event = DetermineNamespacesEvent()
        assert event is not None

    def test_follow_up_question_hitl_invoke(self):
        """Test creating a FollowUpQuestionHitl request via invoke."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3"]}
        request = FollowUpQuestionHitl.invoke(
            question="What topic are you interested in?",
            available_namespaces=available,
        )
        assert request.question == "What topic are you interested in?"
        assert request.available_namespaces == available

    def test_namespace_approval_hitl_invoke(self):
        """Test creating a NamespaceApprovalHitl request via invoke."""
        proposed = {"bucket1": "ns1", "bucket2": "ns2"}
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns2", "ns3"]}
        request = NamespaceApprovalHitl.invoke(
            question="Approve these namespaces?",
            proposed_namespaces=proposed,
            available_namespaces=available,
        )
        assert request.question == "Approve these namespaces?"
        assert request.proposed_namespaces == proposed
        assert request.available_namespaces == available


class TestConfig:
    """Tests for configuration."""

    def test_config_creation_requires_llm(self):
        """Test that config requires LLM configuration."""
        # This test verifies the config structure - actual LLMConfig creation
        # requires LiteLLM proxy settings, so we just check the field exists
        assert hasattr(NamespaceSelectionAgentConfig, "model_fields")
        assert "llm" in NamespaceSelectionAgentConfig.model_fields
        assert "bucket_names" in NamespaceSelectionAgentConfig.model_fields
        assert "rag_delegation" in NamespaceSelectionAgentConfig.model_fields
