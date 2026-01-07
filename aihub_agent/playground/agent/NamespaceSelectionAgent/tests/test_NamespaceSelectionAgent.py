"""Tests for NamespaceSelectionAgent.

These tests verify the NamespaceSelectionAgent correctly handles namespace selection.
Note: Full integration tests require Redis, NATS, and MongoDB infrastructure.
"""

from unittest.mock import MagicMock

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.agents.NamespaceSelectionAgent.configs import NamespaceSelectionAgentConfig
from aihub_agent.agents.NamespaceSelectionAgent.configs.RAGDelegationConfig import RAGDelegationConfig
from aihub_agent.agents.NamespaceSelectionAgent.events import (
    NamespaceSelectionHitl,
    SelectionStoredEvent,
)
from aihub_agent.agents.NamespaceSelectionAgent.NamespaceSelectionAgent import (
    _format_selection_question,
    _format_selection_summary,
    _get_default_selection,
    _parse_namespace_selection,
    _validate_selection,
)


def _create_test_config() -> NamespaceSelectionAgentConfig:
    """Create a test config for NamespaceSelectionAgent."""
    return NamespaceSelectionAgentConfig(
        agent_id="test_namespace_agent",
        agent_class=NamespaceSelectionAgent.__name__,
        name=LocaleString(en="Test Agent"),
        description=LocaleString(en="Test description"),
        bucket_names=["defaultknowledge"],
        rag_delegation=RAGDelegationConfig(
            rag_agent_class="RAGAgent",
            rag_agent_id="test_rag",
        ),
    )


class TestNamespaceSelectionParsing:
    """Tests for parsing user namespace selection."""

    def test_parse_numeric_selection(self):
        """Test parsing numeric selection like '1, 2'."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3", "ns4"]}
        result = _parse_namespace_selection("1, 2", available)
        assert result == {"bucket1": "ns1", "bucket2": "ns4"}

    def test_parse_name_selection(self):
        """Test parsing namespace names directly."""
        available = {"bucket1": ["namespace_a", "namespace_b"]}
        result = _parse_namespace_selection("namespace_b", available)
        assert result == {"bucket1": "namespace_b"}

    def test_parse_mixed_selection(self):
        """Test parsing mix of numbers and names."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3", "ns4"]}
        result = _parse_namespace_selection("ns2", available)
        assert result.get("bucket1") == "ns2"


class TestNamespaceSelectionValidation:
    """Tests for validating namespace selection."""

    def test_valid_selection(self):
        """Test that a valid selection passes."""
        available = {"bucket1": ["ns1", "ns2"]}
        selected = {"bucket1": "ns1"}
        assert _validate_selection(selected, available) is True

    def test_invalid_selection_missing_bucket(self):
        """Test that missing bucket fails validation."""
        available = {"bucket1": ["ns1"], "bucket2": ["ns2"]}
        selected = {"bucket1": "ns1"}
        assert _validate_selection(selected, available) is False

    def test_invalid_selection_wrong_namespace(self):
        """Test that wrong namespace fails validation."""
        available = {"bucket1": ["ns1", "ns2"]}
        selected = {"bucket1": "ns3"}
        assert _validate_selection(selected, available) is False


class TestDefaultSelection:
    """Tests for default namespace selection."""

    def test_get_default_selection(self):
        """Test getting first namespace from each bucket."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3", "ns4"]}
        result = _get_default_selection(available)
        assert result == {"bucket1": "ns1", "bucket2": "ns3"}


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_selection_summary(self):
        """Test formatting a selection summary."""
        selected = {"bucket1": "ns1"}
        t = MagicMock()
        t.side_effect = lambda x: x
        result = _format_selection_summary(selected, t)
        assert "bucket1" in result
        assert "ns1" in result

    def test_format_selection_question(self):
        """Test formatting a selection question."""
        available = {"bucket1": ["ns1", "ns2"]}
        prompt = LocaleString(en="Please select:")
        t = MagicMock()
        t.side_effect = lambda x: str(x) if isinstance(x, LocaleString) else x
        t.extract = lambda x: str(x) if isinstance(x, LocaleString) else x
        result = _format_selection_question(available, prompt, t)
        assert "bucket1" in result
        assert "ns1" in result
        assert "ns2" in result


class TestEvents:
    """Tests for event definitions."""

    def test_selection_stored_event_creation(self):
        """Test creating a SelectionStoredEvent."""
        event = SelectionStoredEvent(selected_namespaces={"bucket1": "ns1"})
        assert event.selected_namespaces == {"bucket1": "ns1"}

    def test_namespace_selection_hitl_invoke(self):
        """Test creating a NamespaceSelectionRequestEvent via invoke."""
        request = NamespaceSelectionHitl.invoke(
            question="Select namespace",
        )
        assert request.question == "Select namespace"


class TestConfig:
    """Tests for configuration."""

    def test_config_creation(self):
        """Test creating a valid config."""
        config = _create_test_config()
        assert config.bucket_names == ["defaultknowledge"]
        assert config.rag_delegation.rag_agent_class == "RAGAgent"
