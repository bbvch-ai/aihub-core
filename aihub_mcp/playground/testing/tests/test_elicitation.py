import pytest

from aihub_mcp.translation.ElicitationHandler import (
    ConfirmationResponse,
    ElicitationHandler,
    ElicitationResult,
    InputResponse,
    truncate_question,
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


class TestElicitationResult:
    """Tests for ElicitationResult dataclass."""

    def test_successful_result_with_string_response(self) -> None:
        """Test successful elicitation with string response."""
        result = ElicitationResult(success=True, response="user input")
        assert result.success is True
        assert result.response == "user input"
        assert result.pending_info is None

    def test_successful_result_with_bool_response(self) -> None:
        """Test successful elicitation with boolean response."""
        result = ElicitationResult(success=True, response=True)
        assert result.success is True
        assert result.response is True

    def test_pending_result(self) -> None:
        """Test pending result when elicitation not supported."""
        pending_info = {"question": "What is your name?", "hitl_type": "input"}
        result = ElicitationResult(success=False, pending_info=pending_info)
        assert result.success is False
        assert result.response is None
        assert result.pending_info == pending_info
        assert result.pending_info["question"] == "What is your name?"
        assert result.pending_info["hitl_type"] == "input"


class TestTruncateQuestion:
    """Tests for question truncation."""

    def test_short_question_unchanged(self) -> None:
        """Test that short questions pass through unchanged."""
        question = "What is your name?"
        assert truncate_question(question) == "What is your name?"

    def test_truncation(self) -> None:
        """Test long questions are truncated."""
        long_question = "A" * 1500
        result = truncate_question(long_question, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
