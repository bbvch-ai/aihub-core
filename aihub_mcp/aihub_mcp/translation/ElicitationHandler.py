"""Handle HITL requests via MCP elicitation."""

import logging
from dataclasses import dataclass
from typing import Any

from fastmcp import Context

logger = logging.getLogger(__name__)


@dataclass
class InputResponse:
    """Response type for text input elicitation."""

    text: str


@dataclass
class ConfirmationResponse:
    """Response type for confirmation elicitation."""

    confirmed: bool


class ElicitationHandler:
    """
    Translates SAAP HumanInTheLoopRequestEvent to MCP elicitation.

    When an agent workflow needs human input or approval, this handler:
    1. Detects the HITL request type (input or confirmation)
    2. Translates to appropriate MCP elicitation request
    3. Receives the user's response
    4. Returns it for publishing back to SAAP
    """

    async def handle_request(
        self,
        ctx: Context,
        request_event: dict[str, Any],
    ) -> str | bool:
        """
        Handle a HITL request by triggering MCP elicitation.

        Returns the user's response (string for input, bool for confirmation).
        """
        question = request_event.get("question", "Please provide input:")
        hitl_type = request_event.get("hitl_type", "input")

        logger.info(f"Handling HITL request: type={hitl_type}, question={question[:50]}...")

        if hitl_type == "confirmation":
            return await self._handle_confirmation(ctx, question)
        else:
            return await self._handle_input(ctx, question)

    async def _handle_input(self, ctx: Context, question: str) -> str:
        """Handle a free-form text input request."""
        try:
            # Use MCP elicitation to get user input
            result = await ctx.elicit(
                message=question,
                response_type=InputResponse,
            )

            if result.action == "accept" and result.data:
                return result.data.text
            elif result.action == "decline":
                return "[User declined to provide input]"
            else:  # cancel
                return "[User cancelled the request]"

        except Exception as e:
            logger.error(f"Elicitation failed: {e}")
            # Fallback: log and return empty
            await ctx.warning(f"HITL Input request: {question}")
            return "[Elicitation not supported by client]"

    async def _handle_confirmation(self, ctx: Context, question: str) -> bool:
        """Handle a yes/no confirmation request."""
        try:
            # Use MCP elicitation to get confirmation
            result = await ctx.elicit(
                message=question,
                response_type=ConfirmationResponse,
            )

            if result.action == "accept" and result.data:
                return result.data.confirmed
            elif result.action == "decline":
                return False
            else:  # cancel
                return False

        except Exception as e:
            logger.error(f"Elicitation failed: {e}")
            # Fallback: log and return False
            await ctx.warning(f"HITL Confirmation request: {question}")
            return False
