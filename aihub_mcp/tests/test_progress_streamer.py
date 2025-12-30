from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_mcp.translation.ProgressStreamer import ProgressStreamer


class TestProgressStreamer:
    """Tests for ProgressStreamer class."""

    @pytest.fixture
    def streamer(self) -> ProgressStreamer:
        """Create a progress streamer for testing."""
        return ProgressStreamer()

    @pytest.fixture
    def mock_ctx(self) -> MagicMock:
        """Create a mock MCP Context."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()
        ctx.debug = AsyncMock()
        ctx.info = AsyncMock()
        return ctx

    def test_initial_counters(self, streamer: ProgressStreamer) -> None:
        """Test that counters start at zero."""
        assert streamer._chunk_count == 0
        assert streamer._thought_count == 0

    @pytest.mark.asyncio
    async def test_stream_chunk_increments_counter(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that streaming a chunk increments the counter."""
        await streamer.stream_chunk(mock_ctx, "Hello")
        assert streamer._chunk_count == 1

        await streamer.stream_chunk(mock_ctx, "World")
        assert streamer._chunk_count == 2

    @pytest.mark.asyncio
    async def test_stream_chunk_reports_progress(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that streaming a chunk reports progress."""
        await streamer.stream_chunk(mock_ctx, "Content")

        mock_ctx.report_progress.assert_called_once_with(
            progress=1,
            total=None,
        )

    @pytest.mark.asyncio
    async def test_stream_chunk_logs_content(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that non-empty chunks are logged."""
        await streamer.stream_chunk(mock_ctx, "Some content")

        mock_ctx.debug.assert_called_once()
        call_args = mock_ctx.debug.call_args[0][0]
        assert "[Chunk 1]" in call_args
        assert "Some content" in call_args

    @pytest.mark.asyncio
    async def test_stream_chunk_skips_empty_content(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that empty/whitespace chunks are not logged."""
        await streamer.stream_chunk(mock_ctx, "   ")

        # Progress is still reported
        mock_ctx.report_progress.assert_called_once()
        # But debug is not called for empty content
        mock_ctx.debug.assert_not_called()

    @pytest.mark.asyncio
    async def test_stream_thought_increments_counter(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that streaming a thought increments the counter."""
        await streamer.stream_thought(mock_ctx, "Reasoning...")
        assert streamer._thought_count == 1

        await streamer.stream_thought(mock_ctx, "More reasoning...")
        assert streamer._thought_count == 2

    @pytest.mark.asyncio
    async def test_stream_thought_reports_progress(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that streaming a thought reports progress."""
        await streamer.stream_thought(mock_ctx, "Thinking...")

        mock_ctx.report_progress.assert_called_once_with(
            progress=1,
            total=None,
        )

    @pytest.mark.asyncio
    async def test_stream_thought_logs_reasoning(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that reasoning is logged via info."""
        await streamer.stream_thought(mock_ctx, "Let me think about this...")

        mock_ctx.info.assert_called_once()
        call_args = mock_ctx.info.call_args[0][0]
        assert "[Reasoning]" in call_args
        assert "Let me think about this" in call_args

    @pytest.mark.asyncio
    async def test_stream_thought_skips_empty_reasoning(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that empty reasoning is not logged."""
        await streamer.stream_thought(mock_ctx, "")

        mock_ctx.report_progress.assert_called_once()
        mock_ctx.info.assert_not_called()

    def test_reset_clears_counters(self, streamer: ProgressStreamer) -> None:
        """Test that reset clears all counters."""
        streamer._chunk_count = 10
        streamer._thought_count = 5

        streamer.reset()

        assert streamer._chunk_count == 0
        assert streamer._thought_count == 0

    @pytest.mark.asyncio
    async def test_chunk_and_thought_independent_counters(
        self, streamer: ProgressStreamer, mock_ctx: MagicMock
    ) -> None:
        """Test that chunk and thought counters are independent."""
        await streamer.stream_chunk(mock_ctx, "Chunk 1")
        await streamer.stream_chunk(mock_ctx, "Chunk 2")
        await streamer.stream_thought(mock_ctx, "Thought 1")

        assert streamer._chunk_count == 2
        assert streamer._thought_count == 1

    @pytest.mark.asyncio
    async def test_long_content_truncated_in_log(self, streamer: ProgressStreamer, mock_ctx: MagicMock) -> None:
        """Test that long chunk content is truncated in log."""
        long_content = "x" * 200
        await streamer.stream_chunk(mock_ctx, long_content)

        call_args = mock_ctx.debug.call_args[0][0]
        # Content should be truncated to 100 chars
        assert len(call_args) < len(long_content) + 20  # Some prefix included
