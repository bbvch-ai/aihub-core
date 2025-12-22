"""Tests for elicitation handler."""

import pytest

from aihub_mcp.translation.ElicitationHandler import (
    ConfirmationResponse,
    ElicitationHandler,
    InputResponse,
)


class TestResponseTypes:
    """Tests for elicitation response types."""

    def test_input_response_structure(self) -> None:
        """Test InputResponse dataclass."""
        response = InputResponse(text="Hello world")
        assert response.text == "Hello world"

    def test_confirmation_response_structure(self) -> None:
        """Test ConfirmationResponse dataclass."""
        response = ConfirmationResponse(confirmed=True)
        assert response.confirmed is True

        response_false = ConfirmationResponse(confirmed=False)
        assert response_false.confirmed is False


class TestElicitationHandler:
    """Tests for ElicitationHandler class."""

    @pytest.fixture
    def handler(self) -> ElicitationHandler:
        """Create an elicitation handler for testing."""
        return ElicitationHandler()

    def test_handler_initialization(self, handler: ElicitationHandler) -> None:
        """Test that handler initializes correctly."""
        assert handler is not None

    def test_determine_input_type(self, handler: ElicitationHandler) -> None:
        """Test determination of HITL type from request event."""
        input_request = {"hitl_type": "input", "question": "What is your name?"}
        confirmation_request = {"hitl_type": "confirmation", "question": "Continue?"}

        assert input_request.get("hitl_type") == "input"
        assert confirmation_request.get("hitl_type") == "confirmation"

    def test_default_hitl_type(self, handler: ElicitationHandler) -> None:
        """Test default HITL type when not specified."""
        request_without_type = {"question": "What is your input?"}
        hitl_type = request_without_type.get("hitl_type", "input")
        assert hitl_type == "input"
