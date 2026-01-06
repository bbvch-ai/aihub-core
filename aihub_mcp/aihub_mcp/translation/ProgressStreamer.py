from fastmcp import Context


class ProgressStreamer:
    """
    Streams SAAP DisplayEvents as MCP progress notifications.

    Translates ChunkEvent and ThoughtEvent to MCP progress updates, keeping
    clients informed during long-running agent executions.
    """

    def __init__(self) -> None:
        self._chunk_count: int = 0
        self._thought_count: int = 0

    async def stream_chunk(self, ctx: Context, content: str) -> None:
        """Stream a ChunkEvent (streaming LLM output) as progress notification."""
        self._chunk_count += 1

        await ctx.report_progress(progress=self._chunk_count, total=None)

        if content.strip():
            await ctx.debug(f"[Chunk {self._chunk_count}] {content[:100]}")

    async def stream_thought(self, ctx: Context, reasoning: str) -> None:
        """Stream a ThoughtEvent (agent reasoning) as progress notification."""
        self._thought_count += 1

        await ctx.report_progress(progress=self._thought_count, total=None)

        if reasoning:
            await ctx.info(f"[Reasoning] {reasoning[:200]}")

    def reset(self) -> None:
        """Reset counters for a new execution."""
        self._chunk_count = 0
        self._thought_count = 0
