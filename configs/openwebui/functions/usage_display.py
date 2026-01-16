"""
AI-Hub Usage Display Filter for Open-WebUI

This filter displays user's LLM usage and budget information at the end of all LLM responses.
It queries the AI-Hub API to get current spend and shows warnings when approaching limits.

Features:
- Shows usage percentage and spend after each LLM response (agents and direct models)
- Displays warning when usage exceeds 80% of budget
- Shows error message when budget is exceeded
- Works with all models routed through LiteLLM (AI-Hub agents and OpenAI pipeline)
"""

import logging
import os
from typing import Any, Callable, Awaitable

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Filter:
    """
    Usage Display Filter - Shows budget usage information after all LLM responses.

    This filter integrates with AI-Hub's usage API to display real-time budget
    consumption to users, helping them stay aware of their usage limits.
    Works for both AI-Hub agents and direct LLM access via OpenAI pipeline.
    """

    class Valves(BaseModel):
        """Configuration settings for the usage display filter."""

        AIHUB_BASE_URL: str = Field(
            default=os.getenv("AIHUB_BASE_URL", "http://localhost:8000"),
            description="Base URL for the AI-Hub API",
        )
        AIHUB_SUPERUSER_API_KEY: str = Field(
            default=os.getenv("AIHUB_SUPERUSER_API_KEY", ""),
            description="API key for authenticating with AI-Hub",
        )
        SHOW_USAGE_THRESHOLD: float = Field(
            default=float(os.getenv("SHOW_USAGE_THRESHOLD", "0.5")),
            description="Show usage info when spend exceeds this percentage (0.0-1.0) of budget",
        )
        WARNING_THRESHOLD: float = Field(
            default=float(os.getenv("WARNING_THRESHOLD", "0.8")),
            description="Show warning when spend exceeds this percentage (0.0-1.0) of budget",
        )
        ENABLED: bool = Field(
            default=os.getenv("USAGE_DISPLAY_ENABLED", "true").lower() == "true",
            description="Enable or disable usage display",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def outlet(
        self,
        body: dict[str, Any],
        __user__: dict[str, Any],
        __event_emitter__: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        """
        Post-processing filter that appends usage information to responses.

        Called after the model response is generated. Fetches usage data from
        AI-Hub API and appends a usage summary if thresholds are exceeded.
        Works for all models (AI-Hub agents and direct LLM access).
        """
        if not self.valves.ENABLED:
            return body

        try:
            usage = await self._fetch_user_usage(__user__)
            if usage:
                usage_message = self._format_usage_message(usage)
                if usage_message:
                    body = self._append_usage_to_response(body, usage_message)
        except Exception as e:
            logger.warning(f"Failed to fetch usage information: {e}")

        return body

    async def _fetch_user_usage(self, user: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch user's usage information from AI-Hub API."""
        if not self.valves.AIHUB_SUPERUSER_API_KEY:
            logger.debug("No API key configured, skipping usage fetch")
            return None

        headers = {
            "Authorization": f"Bearer {self.valves.AIHUB_SUPERUSER_API_KEY}",
            "X-OpenWebUI-User-Email": user.get("email", ""),
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.valves.AIHUB_BASE_URL}/api/v1/usage/me",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    def _format_usage_message(self, usage: dict[str, Any]) -> str | None:
        """
        Format usage information into a user-friendly message.

        Returns None if usage is below the display threshold or if no budget is set.
        """
        spend = usage.get("spend", 0)
        max_budget = usage.get("max_budget")
        usage_percent = usage.get("usage_percent")
        is_approaching_limit = usage.get("is_approaching_limit", False)
        is_over_limit = usage.get("is_over_limit", False)
        budget_reset_at = usage.get("budget_reset_at")

        # No budget set - don't show anything
        if max_budget is None or max_budget <= 0:
            return None

        # Below display threshold - don't show
        if usage_percent is not None and usage_percent < (self.valves.SHOW_USAGE_THRESHOLD * 100):
            return None

        # Format the message based on status
        if is_over_limit:
            return (
                f"\n\n---\n"
                f"🚫 **Budget Exceeded**: ${spend:.2f} / ${max_budget:.2f} "
                f"({usage_percent:.0f}%)\n"
                f"_Your usage limit has been reached. Please contact your administrator._"
            )
        elif is_approaching_limit:
            reset_info = f" Resets: {budget_reset_at}" if budget_reset_at else ""
            return (
                f"\n\n---\n"
                f"⚠️ **Usage Alert**: ${spend:.2f} / ${max_budget:.2f} "
                f"({usage_percent:.0f}%){reset_info}"
            )
        else:
            # Above show threshold but below warning
            return (
                f"\n\n---\n"
                f"📊 **Usage**: ${spend:.2f} / ${max_budget:.2f} ({usage_percent:.0f}%)"
            )

    def _append_usage_to_response(self, body: dict[str, Any], usage_message: str) -> dict[str, Any]:
        """Append usage message to the last assistant message in the response."""
        messages = body.get("messages", [])
        if not messages:
            return body

        # Find the last assistant message
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                content = messages[i].get("content", "")
                if isinstance(content, str):
                    messages[i]["content"] = content + usage_message
                break

        return body
