import html
import logging
import re
from dataclasses import dataclass
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


@dataclass
class ElicitationResult:
    """
    Result of an elicitation attempt.

    When elicitation succeeds (client supports it), success=True and response contains the user's answer.
    When elicitation fails (client doesn't support it), success=False and pending_info contains
    the question and type for the two-phase fallback flow.
    """

    success: bool
    response: str | bool | None = None
    pending_info: dict[str, Any] | None = None


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

    When elicitation is not supported by the MCP client, returns an ElicitationResult
    with success=False and pending_info for the two-phase fallback flow.
    """

    async def handle_request(
        self,
        ctx: Context,
        request_event: dict[str, Any],
    ) -> ElicitationResult:
        """Handle a HITL request via MCP elicitation, returning success or pending result."""
        raw_question = request_event.get("question", "Please provide input:")
        hitl_type = request_event.get("hitl_type", "input")
        question = sanitize_question(raw_question)

        logger.info(f"Handling HITL request: type={hitl_type}, question={question[:50]}...")

        if hitl_type == "confirmation":
            return await self._handle_confirmation(ctx, question, hitl_type)
        else:
            return await self._handle_input(ctx, question, hitl_type)

    async def _handle_input(self, ctx: Context, question: str, hitl_type: str) -> ElicitationResult:
        """Handle a free-form text input request."""
        try:
            logger.debug(f"Calling ctx.elicit for input: {question[:50]}...")
            result = await ctx.elicit(
                message=question,
                response_type=InputResponse,  # type: ignore[arg-type]
            )
            logger.debug(f"Elicitation result: action={result.action}")

            if result.action == "accept" and result.data:
                data: Any = result.data
                logger.info(f"User provided input: {str(data.text)[:50]}...")
                return ElicitationResult(success=True, response=str(data.text))
            elif result.action == "decline":
                logger.info("User declined to provide input")
                return ElicitationResult(success=True, response="[User declined to provide input]")
            else:
                logger.info("User cancelled the request")
                return ElicitationResult(success=True, response="[User cancelled the request]")

        except Exception as e:
            logger.warning(f"Elicitation not supported by client: {e}")
            return ElicitationResult(
                success=False,
                pending_info={
                    "question": question,
                    "hitl_type": hitl_type,
                },
            )

    async def _handle_confirmation(self, ctx: Context, question: str, hitl_type: str) -> ElicitationResult:
        """Handle a yes/no confirmation request."""
        try:
            logger.debug(f"Calling ctx.elicit for confirmation: {question[:50]}...")
            result = await ctx.elicit(
                message=question,
                response_type=ConfirmationResponse,  # type: ignore[arg-type]
            )

            if result.action == "accept" and result.data:
                data: Any = result.data
                logger.info(f"User confirmed: {data.confirmed}")
                return ElicitationResult(success=True, response=bool(data.confirmed))
            elif result.action == "decline":
                logger.info("User declined confirmation")
                return ElicitationResult(success=True, response=False)
            else:
                logger.info("User cancelled confirmation")
                return ElicitationResult(success=True, response=False)

        except Exception as e:
            logger.warning(f"Elicitation not supported by client: {e}")
            return ElicitationResult(
                success=False,
                pending_info={
                    "question": question,
                    "hitl_type": hitl_type,
                },
            )
