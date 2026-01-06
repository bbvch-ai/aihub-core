import logging
from typing import Any

from fastmcp import Context

logger = logging.getLogger(__name__)


class SamplingBridge:
    """
    Routes LLM completion requests from agents to the MCP client's LLM.

    When an agent needs a completion (SamplingRequestEvent), this bridge calls
    ctx.sample() to leverage the client's model for cost, privacy, or capability reasons.
    """

    async def handle_sampling_request(
        self,
        ctx: Context,
        request: dict[str, Any],
    ) -> str:
        """Handle a sampling request from an agent by calling ctx.sample()."""
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens")
        system_prompt = request.get("system_prompt")

        logger.info(f"Handling sampling request: {len(messages)} messages")

        try:
            formatted_messages = self._format_messages(messages)

            # ctx.sample expects string or Sequence[SamplingMessage]
            result = await ctx.sample(
                messages=formatted_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

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
        """Format messages for ctx.sample() which accepts string or list."""
        if len(messages) == 1:
            msg = messages[0]
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return " ".join(block.get("text", "") for block in content if block.get("type") == "text")
            return str(content)

        return messages
