"""Tests for sampling bridge."""

import pytest

from aihub_mcp.translation.SamplingBridge import SamplingBridge


class TestSamplingBridge:
    """Tests for SamplingBridge class."""

    @pytest.fixture
    def bridge(self) -> SamplingBridge:
        """Create a sampling bridge for testing."""
        return SamplingBridge()

    def test_bridge_initialization(self, bridge: SamplingBridge) -> None:
        """Test that bridge initializes correctly."""
        assert bridge is not None

    def test_format_single_message(self, bridge: SamplingBridge) -> None:
        """Test formatting a single message for sampling."""
        messages = [{"role": "user", "content": "Hello"}]
        result = bridge._format_messages(messages)
        assert result == "Hello"

    def test_format_multiple_messages(self, bridge: SamplingBridge) -> None:
        """Test formatting multiple messages for sampling."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        result = bridge._format_messages(messages)
        assert result == messages  # Multiple messages returned as list

    def test_format_empty_messages(self, bridge: SamplingBridge) -> None:
        """Test formatting empty message list."""
        messages: list[dict[str, str]] = []
        result = bridge._format_messages(messages)
        assert result == messages

    def test_format_multipart_content(self, bridge: SamplingBridge) -> None:
        """Test formatting message with multipart content."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "text", "text": "world"},
                ],
            }
        ]
        result = bridge._format_messages(messages)
        assert result == "Hello  world"


class TestSamplingRequest:
    """Tests for sampling request handling."""

    def test_extract_request_params(self) -> None:
        """Test extracting parameters from sampling request."""
        request = {
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 100,
            "system_prompt": "You are helpful",
        }

        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens")
        system_prompt = request.get("system_prompt")

        assert len(messages) == 1
        assert max_tokens == 100
        assert system_prompt == "You are helpful"

    def test_extract_request_defaults(self) -> None:
        """Test extracting parameters with defaults."""
        request = {"messages": [{"role": "user", "content": "Test"}]}

        max_tokens = request.get("max_tokens")
        system_prompt = request.get("system_prompt")

        assert max_tokens is None
        assert system_prompt is None
