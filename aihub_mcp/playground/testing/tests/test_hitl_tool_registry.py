from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_mcp.server.HITLToolRegistry import HITLToolRegistry


class TestHITLToolRegistry:
    """Tests for HITLToolRegistry."""

    @pytest.fixture
    def mock_mcp_server(self) -> MagicMock:
        """Create a mock MCP server."""
        server = MagicMock()
        server.mcp = MagicMock()
        server.mcp.tool = MagicMock(return_value=lambda fn: fn)
        return server

    @pytest.fixture
    def mock_event_translator(self) -> MagicMock:
        """Create a mock event translator."""
        translator = MagicMock()
        translator.resume_after_hitl = AsyncMock(return_value="Agent completed successfully")
        return translator

    @pytest.fixture
    def registry(self, mock_mcp_server: MagicMock, mock_event_translator: MagicMock) -> HITLToolRegistry:
        """Create a HITLToolRegistry with mocks."""
        return HITLToolRegistry(
            mcp_server=mock_mcp_server,
            event_translator=mock_event_translator,
        )

    def test_initialization(self, registry: HITLToolRegistry, mock_mcp_server: MagicMock) -> None:
        """Test registry initializes correctly."""
        assert registry._mcp_server == mock_mcp_server

    def test_register_tools_creates_submit_hitl_response(
        self, registry: HITLToolRegistry, mock_mcp_server: MagicMock
    ) -> None:
        """Test that register_tools creates the submit_hitl_response tool."""
        registry.register_tools()

        # Verify mcp.tool was called with correct parameters
        mock_mcp_server.mcp.tool.assert_called_once()
        call_kwargs = mock_mcp_server.mcp.tool.call_args[1]
        assert call_kwargs["name"] == "submit_hitl_response"
        assert "human response" in call_kwargs["description"].lower()


class TestSubmitHITLResponseTool:
    """Tests for the submit_hitl_response tool behavior."""

    @pytest.fixture
    def mock_ctx(self) -> MagicMock:
        """Create a mock MCP context."""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_successful_submission(self) -> None:
        """Test successful HITL response submission."""
        mock_event_translator = MagicMock()
        mock_event_translator.resume_after_hitl = AsyncMock(return_value="Final result")

        mock_mcp_server = MagicMock()
        captured_tool_fn = None

        def capture_tool(**kwargs):
            def decorator(fn):
                nonlocal captured_tool_fn
                captured_tool_fn = fn
                return fn

            return decorator

        mock_mcp_server.mcp.tool = capture_tool

        registry = HITLToolRegistry(
            mcp_server=mock_mcp_server,
            event_translator=mock_event_translator,
        )
        registry.register_tools()

        # Now test the captured tool function
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()

        result = await captured_tool_fn("test_request_id", "user response", mock_ctx)

        assert result == "Final result"
        mock_event_translator.resume_after_hitl.assert_called_once_with(
            request_id="test_request_id",
            response="user response",
            ctx=mock_ctx,
        )

    @pytest.mark.asyncio
    async def test_invalid_request_id_returns_error(self) -> None:
        """Test that invalid request_id returns error message."""
        mock_event_translator = MagicMock()
        mock_event_translator.resume_after_hitl = AsyncMock(
            side_effect=ValueError("Pending HITL request not found or expired")
        )

        mock_mcp_server = MagicMock()
        captured_tool_fn = None

        def capture_tool(**kwargs):
            def decorator(fn):
                nonlocal captured_tool_fn
                captured_tool_fn = fn
                return fn

            return decorator

        mock_mcp_server.mcp.tool = capture_tool

        registry = HITLToolRegistry(
            mcp_server=mock_mcp_server,
            event_translator=mock_event_translator,
        )
        registry.register_tools()

        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.warning = AsyncMock()

        result = await captured_tool_fn("invalid_id", "response", mock_ctx)

        assert "Error:" in result
        assert "not found or expired" in result

    @pytest.mark.asyncio
    async def test_store_not_configured_returns_error(self) -> None:
        """Test that missing store configuration returns error."""
        mock_event_translator = MagicMock()
        mock_event_translator.resume_after_hitl = AsyncMock(
            side_effect=RuntimeError("HITL pending store not configured")
        )

        mock_mcp_server = MagicMock()
        captured_tool_fn = None

        def capture_tool(**kwargs):
            def decorator(fn):
                nonlocal captured_tool_fn
                captured_tool_fn = fn
                return fn

            return decorator

        mock_mcp_server.mcp.tool = capture_tool

        registry = HITLToolRegistry(
            mcp_server=mock_mcp_server,
            event_translator=mock_event_translator,
        )
        registry.register_tools()

        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()

        result = await captured_tool_fn("some_id", "response", mock_ctx)

        assert "Error:" in result
        assert "not configured" in result
