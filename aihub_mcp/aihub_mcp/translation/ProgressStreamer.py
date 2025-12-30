import logging
import re

from fastmcp import Context

logger = logging.getLogger(__name__)

# Patterns for sensitive data that should be masked in logs
SENSITIVE_PATTERNS = [
    # API keys and tokens
    (re.compile(r"(api[_-]?key|token|bearer|authorization)[\"']?\s*[:=]\s*[\"']?[\w\-\.]+", re.I), "[MASKED_KEY]"),
    # Passwords
    (re.compile(r"(password|passwd|pwd|secret)[\"']?\s*[:=]\s*[\"']?[^\s\"']+", re.I), "[MASKED_PASSWORD]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[MASKED_EMAIL]"),
    # Credit card numbers
    (re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"), "[MASKED_CARD]"),
    # Social security numbers
    (re.compile(r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b"), "[MASKED_SSN]"),
    # JWT tokens
    (re.compile(r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*"), "[MASKED_JWT]"),
]


class ProgressStreamer:
    """
    Streams SAAP DisplayEvents as MCP progress notifications.

    Translates:
    - ChunkEvent → Progress with partial content
    - ThoughtEvent → Progress with reasoning metadata

    This keeps MCP clients informed during long-running agent executions.

    Security: Optionally masks sensitive data in logged content.
    """

    def __init__(self, mask_sensitive_data: bool = True) -> None:
        self._chunk_count: int = 0
        self._thought_count: int = 0
        self._mask_sensitive_data = mask_sensitive_data

    def _mask_content(self, content: str) -> str:
        """Mask potentially sensitive data in content for logging."""
        if not self._mask_sensitive_data:
            return content

        masked = content
        for pattern, replacement in SENSITIVE_PATTERNS:
            masked = pattern.sub(replacement, masked)
        return masked

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

        # Also log the content for visibility (with masking)
        # Note: MCP progress doesn't have a content field,
        # so we use debug logging to surface the chunk
        if content.strip():
            safe_content = self._mask_content(content[:100])
            await ctx.debug(f"[Chunk {self._chunk_count}] {safe_content}")

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

        # Log the reasoning for visibility (with masking)
        if reasoning:
            safe_reasoning = self._mask_content(reasoning[:200])
            await ctx.info(f"[Reasoning] {safe_reasoning}")

    def reset(self) -> None:
        """Reset counters for a new execution."""
        self._chunk_count = 0
        self._thought_count = 0
