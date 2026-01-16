"""
AI-Hub Usage Display Filter for Open-WebUI

This filter displays user's LLM usage and budget information at the end of all LLM responses.
It queries the AI-Hub API to get current spend and shows warnings when approaching limits.

Features:
- Shows usage percentage and spend after each LLM response (agents and direct models)
- Displays warning when usage exceeds 80% of budget
- Shows error message when budget is exceeded
- Works with all models routed through LiteLLM (AI-Hub agents and OpenAI pipeline)
- Multilingual support (en, de, fr, it)
- Configurable date format (European DD.MM.YYYY or US MM/DD/YYYY)
"""

import logging
import os
from datetime import datetime
from typing import Any, Callable, Awaitable, Literal

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Translations for usage messages
TRANSLATIONS = {
    "en": {
        "usage": "Usage",
        "usage_alert": "Usage Alert",
        "budget_exceeded": "Budget Exceeded",
        "resets": "Resets",
        "limit_reached": "Your usage limit has been reached. Please contact your administrator.",
    },
    "de": {
        "usage": "Nutzung",
        "usage_alert": "Nutzungswarnung",
        "budget_exceeded": "Budget überschritten",
        "resets": "Zurücksetzung",
        "limit_reached": "Ihr Nutzungslimit wurde erreicht. Bitte kontaktieren Sie Ihren Administrator.",
    },
    "fr": {
        "usage": "Utilisation",
        "usage_alert": "Alerte d'utilisation",
        "budget_exceeded": "Budget dépassé",
        "resets": "Réinitialisation",
        "limit_reached": "Votre limite d'utilisation a été atteinte. Veuillez contacter votre administrateur.",
    },
    "it": {
        "usage": "Utilizzo",
        "usage_alert": "Avviso di utilizzo",
        "budget_exceeded": "Budget superato",
        "resets": "Reset",
        "limit_reached": "Il limite di utilizzo è stato raggiunto. Contatta il tuo amministratore.",
    },
}


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
        SHOW_AMOUNTS: bool = Field(
            default=os.getenv("USAGE_SHOW_AMOUNTS", "true").lower() == "true",
            description="Show dollar amounts (e.g., $25.00 / $50.00). If false, only shows percentage.",
        )
        LOCALE: Literal["en", "de", "fr", "it"] = Field(
            default=os.getenv("USAGE_DISPLAY_LOCALE", "en"),
            description="Language for usage messages (en, de, fr, it)",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _get_translation(self, key: str) -> str:
        """Get translated string for the current locale."""
        locale = self.valves.LOCALE
        if locale not in TRANSLATIONS:
            locale = "en"
        return TRANSLATIONS[locale].get(key, TRANSLATIONS["en"][key])

    def _format_date(self, date_str: str | None) -> str | None:
        """Format date string according to locale (DD.MM.YYYY for European locales)."""
        if not date_str:
            return None

        try:
            # Try parsing ISO format first (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d")

            # Format based on locale
            if self.valves.LOCALE in ("de", "fr", "it"):
                return dt.strftime("%d.%m.%Y")
            else:
                return dt.strftime("%m/%d/%Y")
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse date '{date_str}': {e}")
            return date_str

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

        # Format reset info with localized date
        formatted_date = self._format_date(budget_reset_at)
        reset_label = self._get_translation("resets")
        reset_info = f" | {reset_label}: {formatted_date}" if formatted_date else ""

        # Format usage display based on SHOW_AMOUNTS setting
        if self.valves.SHOW_AMOUNTS:
            usage_display = f"${spend:.2f} / ${max_budget:.2f} ({usage_percent:.0f}%)"
        else:
            usage_display = f"{usage_percent:.0f}%"

        # Format the message based on status with translations
        if is_over_limit:
            label = self._get_translation("budget_exceeded")
            limit_msg = self._get_translation("limit_reached")
            return f"\n\n---\n🚫 **{label}**: {usage_display}{reset_info}\n_{limit_msg}_"
        elif is_approaching_limit:
            label = self._get_translation("usage_alert")
            return f"\n\n---\n⚠️ **{label}**: {usage_display}{reset_info}"
        else:
            label = self._get_translation("usage")
            return f"\n\n---\n📊 **{label}**: {usage_display}{reset_info}"

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
