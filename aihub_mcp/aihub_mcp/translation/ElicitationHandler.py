import html
import logging
import re
from typing import Any

from fastmcp import Context
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Maximum length for displayed questions
MAX_QUESTION_LENGTH = 1000

# Pattern for potentially dangerous content in questions
DANGEROUS_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.I | re.S),
    re.compile(r"javascript:", re.I),
    re.compile(r"on\w+\s*=", re.I),
]


class InputResponse(BaseModel):
    """Response type for text input elicitation."""

    text: str


class ConfirmationResponse(BaseModel):
    """Response type for confirmation elicitation."""

    confirmed: bool


def sanitize_question(question: str, max_length: int = MAX_QUESTION_LENGTH) -> str:
    """Sanitize a question string by removing dangerous patterns, escaping HTML, and truncating."""
    sanitized = question

    for pattern in DANGEROUS_PATTERNS:
        sanitized = pattern.sub("", sanitized)

    sanitized = html.escape(sanitized)

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


class ElicitationHandler:
    """
    Translates SAAP HumanInTheLoopRequestEvent to MCP elicitation.

    Detects the HITL request type, triggers appropriate MCP elicitation, and
    returns the user's response for publishing back to SAAP.
    """

    async def handle_request(
        self,
        ctx: Context,
        request_event: dict[str, Any],
    ) -> str | bool:
        """Handle a HITL request via MCP elicitation. Returns string for input, bool for confirmation."""
        raw_question = request_event.get("question", "Please provide input:")
        hitl_type = request_event.get("hitl_type", "input")
        question = sanitize_question(raw_question)

        logger.info(f"Handling HITL request: type={hitl_type}, question={question[:50]}...")

        if hitl_type == "confirmation":
            return await self._handle_confirmation(ctx, question)
        else:
            return await self._handle_input(ctx, question)

    async def _handle_input(self, ctx: Context, question: str) -> str:
        """Handle a free-form text input request."""
        try:
            # FastMCP elicit API is experimental, types not fully defined
            result = await ctx.elicit(
                message=question,
                response_type=InputResponse,  # type: ignore[arg-type]
            )

            if result.action == "accept" and result.data:
                data: Any = result.data
                return str(data.text)
            elif result.action == "decline":
                return "[User declined to provide input]"
            else:
                return "[User cancelled the request]"

        except Exception as e:
            logger.error(f"Elicitation failed: {e}")
            await ctx.warning(f"HITL Input request: {question}")
            return "[Elicitation not supported by client]"

    async def _handle_confirmation(self, ctx: Context, question: str) -> bool:
        """Handle a yes/no confirmation request."""
        try:
            # FastMCP elicit API is experimental, types not fully defined
            result = await ctx.elicit(
                message=question,
                response_type=ConfirmationResponse,  # type: ignore[arg-type]
            )

            if result.action == "accept" and result.data:
                data: Any = result.data
                return bool(data.confirmed)
            elif result.action == "decline":
                return False
            else:
                return False

        except Exception as e:
            logger.error(f"Elicitation failed: {e}")
            await ctx.warning(f"HITL Confirmation request: {question}")
            return False
