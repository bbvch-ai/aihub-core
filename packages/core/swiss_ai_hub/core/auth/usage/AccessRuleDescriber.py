from __future__ import annotations

from swiss_ai_hub.core.auth.usage.usage_limit_models import UsageLimitPeriod
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler

_SCOPE_PREFIX = "aihub.user."


class AccessRuleDescriber:
    """Human-readable descriptions for access rule patterns and usage limit periods."""

    @staticmethod
    def describe_pattern(pattern: str, locale: str = LocaleHandler.DEFAULT_LOCALE) -> str:
        """Convert a dotted usage limit pattern to a human-readable scope label.

        Examples:
            ``aihub.user.agent.>``            -> "all agents"
            ``aihub.user.agent.*.*``          -> "all agents"
            ``aihub.user.agent.MyAgent.*``    -> "MyAgent"
            ``aihub.user.agent.MyAgent.v1``   -> "MyAgent/v1"
            ``aihub.user.process.>``          -> "all processes"
        """
        if not pattern.startswith(_SCOPE_PREFIX):
            return pattern

        remainder = pattern[len(_SCOPE_PREFIX) :]
        parts = remainder.split(".", 1)
        resource_type = parts[0]
        suffix = parts[1] if len(parts) > 1 else ""

        if not suffix or all(s in ("*", ">") for s in suffix.split(".")):
            return LocaleHandler(locale)(f"lib.usage.scope.all_{resource_type}s")

        suffix_parts = suffix.split(".")
        if len(suffix_parts) == 2 and suffix_parts[1] in ("*", ">"):
            return suffix_parts[0]

        return "/".join(suffix_parts)

    @staticmethod
    def get_period_label(period: UsageLimitPeriod | None, locale: str = LocaleHandler.DEFAULT_LOCALE) -> str:
        """Get the localized label for a usage period."""
        if period is None:
            return ""
        result = LocaleHandler(locale)(f"lib.usage.periods.{period}")
        # python-i18n returns the key path on miss; fall back to raw period value
        if result.startswith("lib.usage."):
            return period
        return result
