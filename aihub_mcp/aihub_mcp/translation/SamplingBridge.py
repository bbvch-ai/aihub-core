"""Bridge for routing agent LLM requests to MCP client's LLM."""

import logging
from typing import Any

from fastmcp import Context

logger = logging.getLogger(__name__)


class SamplingBridge:
    """
    Routes LLM completion requests from agents to the MCP client's LLM.

    When an agent needs an LLM completion (via a SamplingRequestEvent),
    this bridge:
    1. Intercepts the sampling request
    2. Calls ctx.sample() to use the MCP client's LLM
    3. Returns the completion back to the agent

    This enables agents to leverage the client's model for completions,
    useful for:
    - Cost optimization (use client's existing model)
    - Privacy (data doesn't leave client)
    - Capability (use client's more powerful model)
    """

    async def handle_sampling_request(
        self,
        ctx: Context,
        request: dict[str, Any],
    ) -> str:
        """
        Handle a sampling request from an agent.

        Translates to ctx.sample() and returns the completion.
        """
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens")
        system_prompt = request.get("system_prompt")

        logger.info(f"Handling sampling request: {len(messages)} messages")

        try:
            # Convert messages to format expected by ctx.sample()
            formatted_messages = self._format_messages(messages)

            # Call the MCP client's LLM
            result = await ctx.sample(
                messages=formatted_messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

            # Extract text content from result
            if hasattr(result, "text"):
                return result.text
            elif hasattr(result, "content"):
                return str(result.content)
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            raise RuntimeError(f"LLM sampling failed: {e}") from e

    def _format_messages(self, messages: list[dict[str, Any]]) -> str | list[dict[str, Any]]:
        """Format messages for ctx.sample()."""
        # ctx.sample accepts either a string or list of messages
        if len(messages) == 1:
            # Single message - extract content
            msg = messages[0]
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Handle multi-part content (text + images)
                return " ".join(block.get("text", "") for block in content if block.get("type") == "text")
            return str(content)

        # Multiple messages - return as list
        return messages

    async def is_sampling_supported(self, ctx: Context) -> bool:
        """Check if the MCP client supports sampling."""
        try:
            # Check if sampling capability is available
            # This is a simple heuristic check
            return hasattr(ctx, "sample")
        except Exception:
            return False
