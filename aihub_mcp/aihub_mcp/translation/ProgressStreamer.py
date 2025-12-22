"""Stream SAAP display events as MCP progress notifications."""

import logging

from fastmcp import Context

logger = logging.getLogger(__name__)


class ProgressStreamer:
    """
    Streams SAAP DisplayEvents as MCP progress notifications.

    Translates:
    - ChunkEvent → Progress with partial content
    - ThoughtEvent → Progress with reasoning metadata

    This keeps MCP clients informed during long-running agent executions.
    """

    def __init__(self) -> None:
        self._chunk_count: int = 0
        self._thought_count: int = 0

    async def stream_chunk(self, ctx: Context, content: str) -> None:
        """
        Stream a ChunkEvent as progress notification.

        Chunks represent streaming LLM output (token-by-token).
        """
        self._chunk_count += 1

        # Report progress with chunk number
        # Using chunk count as progress indicator
        await ctx.report_progress(
            progress=self._chunk_count,
            total=None,  # Unknown total for streaming
        )

        # Also log the content for visibility
        # Note: MCP progress doesn't have a content field,
        # so we use info logging to surface the chunk
        if content.strip():
            await ctx.debug(f"[Chunk {self._chunk_count}] {content[:100]}")

    async def stream_thought(self, ctx: Context, reasoning: str) -> None:
        """
        Stream a ThoughtEvent as progress notification.

        Thoughts represent agent reasoning/internal monologue.
        """
        self._thought_count += 1

        # Report progress
        await ctx.report_progress(
            progress=self._thought_count,
            total=None,
        )

        # Log the reasoning for visibility
        if reasoning:
            await ctx.info(f"[Reasoning] {reasoning[:200]}")

    def reset(self) -> None:
        """Reset counters for a new execution."""
        self._chunk_count = 0
        self._thought_count = 0
