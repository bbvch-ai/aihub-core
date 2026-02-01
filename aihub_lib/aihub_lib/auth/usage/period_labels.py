"""Multilingual labels for usage limit periods."""

from __future__ import annotations

import zoneinfo
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aihub_lib.auth.usage.UsageLimitService import UsageLimitPeriod
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString

if TYPE_CHECKING:
    from aihub_lib.auth.usage.UsageLimitService import UsageStatus

_LOCALES = ("en", "de", "fr", "it")

_RESOURCE_PREFIX_SCOPE_KEYS: dict[str, str] = {
    "aihub.user.agent.": "all_agents",
}


def _t(key: str, locale: str, **kwargs: str | int) -> str:
    """Resolve a single i18n key for the given locale."""
    return LocaleHandler(locale)(f"lib.usage.{key}", **kwargs)


def get_period_label(period: UsageLimitPeriod | None, locale: str = "en") -> str:
    """Get the localized label for a usage period."""
    if period is None:
        return ""
    result = _t(f"periods.{period}", locale)
    # python-i18n returns the key path on miss; fall back to raw period value
    if result.startswith("lib.usage."):
        return period
    return result


def _detect_resource_scope(pattern: str) -> tuple[str, str]:
    """Detect the resource prefix and return (suffix, i18n scope key)."""
    for prefix, scope_key in _RESOURCE_PREFIX_SCOPE_KEYS.items():
        if pattern.startswith(prefix):
            return pattern[len(prefix) :], scope_key
    return pattern, "all_resources"


def describe_pattern(pattern: str, locale: str = "en") -> str:
    """Convert a dotted usage limit pattern to a human-readable scope label.

    Examples:
        ``aihub.user.agent.>``            → "all agents"
        ``aihub.user.agent.*.*``          → "all agents"
        ``aihub.user.agent.MyAgent.*``    → "MyAgent"
        ``aihub.user.agent.MyAgent.v1``   → "MyAgent/v1"
        ``aihub.user.process.>``          → "all processes"
    """
    suffix, scope_key = _detect_resource_scope(pattern)

    # Catch-all patterns: ">", "*", "*.*"
    if suffix in (">", "*") or all(p in ("*", ">") for p in suffix.split(".")):
        return _t(f"scope.{scope_key}", locale)

    parts = suffix.split(".")
    # Specific class with wildcard id: "MyAgent.*" → "MyAgent"
    if len(parts) == 2 and parts[1] in ("*", ">"):
        return parts[0]

    # Fully specific: "MyAgent.v1" → "MyAgent/v1"
    return "/".join(parts)


_WEEKDAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _format_reset_label(reset_at: datetime, locale: str) -> str:
    """Build a localized reset label that adapts to how far away the reset is.

    - Same day  → "Resets at 11:35"
    - Tomorrow  → "Resets tomorrow at 11:35"
    - Within 7 days → "Resets on Wednesday at 11:35"
    - Further   → "Resets on 15.02.2025 at 11:35"
    """
    user_tz = zoneinfo.ZoneInfo("Europe/Zurich")
    local_reset = reset_at.astimezone(user_tz)
    local_now = datetime.now(user_tz)
    time_str = local_reset.strftime("%H:%M")

    days_until = (local_reset.date() - local_now.date()).days

    if days_until <= 0:
        return _t("messages.resets_at", locale, time=time_str)
    if days_until == 1:
        return _t("messages.resets_tomorrow_at", locale, time=time_str)
    if days_until <= 6:
        weekday_key = _WEEKDAY_KEYS[local_reset.weekday()]
        weekday_name = _t(f"weekdays.{weekday_key}", locale)
        return _t("messages.resets_on_weekday_at", locale, weekday=weekday_name, time=time_str)

    date_str = local_reset.strftime("%d.%m.%Y")
    return _t("messages.resets_on_date_at", locale, date=date_str, time=time_str)


def build_exceeded_detail(usage_status: UsageStatus, locale: str = "en") -> dict[str, Any]:
    """Build the 429 response detail dict from a UsageStatus.

    The ``message`` field contains a single pre-formatted, locale-aware string
    ready for display. The ``messages`` dict and ``limits`` array are kept for
    backward compatibility.
    """
    error_messages = build_usage_limit_messages(usage_status.limit, usage_status.period)

    reset_at_local = None
    reset_in_seconds = None
    if usage_status.reset_at:
        now = datetime.now(UTC)
        delta = usage_status.reset_at - now
        reset_in_seconds = max(0, int(delta.total_seconds()))

        local_time = usage_status.reset_at.astimezone(zoneinfo.ZoneInfo("Europe/Zurich"))
        reset_at_local = local_time.strftime("%H:%M")

    reset_label = _format_reset_label(usage_status.reset_at, locale) if usage_status.reset_at else None
    message = _build_display_message(usage_status, locale, reset_label)

    return {
        "error": "usage_limit_exceeded",
        "message": message,
        "messages": error_messages.model_dump(),
        "current_count": usage_status.current_count,
        "limit": usage_status.limit,
        "period": usage_status.period,
        "reset_at": usage_status.reset_at.isoformat() if usage_status.reset_at else None,
        "reset_at_local": reset_at_local,
        "reset_in_seconds": reset_in_seconds,
        "limits": [
            {
                "pattern": ls.pattern,
                "scope": {loc: describe_pattern(ls.pattern, loc) for loc in _LOCALES},
                "limit": ls.limit,
                "period": ls.period,
                "period_label": {loc: get_period_label(ls.period, loc) for loc in _LOCALES},
                "current_count": ls.current_count,
                "is_exceeded": ls.is_exceeded,
            }
            for ls in usage_status.limits
        ],
    }


def _build_display_message(usage_status: UsageStatus, locale: str, reset_label: str | None) -> str:
    """Build a single ready-to-display message in the user's locale."""
    exceeded = [ls for ls in usage_status.limits if ls.is_exceeded]

    if exceeded:
        lines: list[str] = []
        for ls in exceeded:
            lines.append(
                _t(
                    "messages.limit_detail",
                    locale,
                    current=ls.current_count,
                    limit=ls.limit,
                    period=get_period_label(ls.period, locale),
                    scope=describe_pattern(ls.pattern, locale),
                )
            )
        msg = _t("messages.limit_exceeded", locale) + ": " + " · ".join(lines)
    else:
        msg = _t("messages.limit_exceeded", locale)

    if reset_label:
        msg += " · " + reset_label

    return msg


def build_warning_message(usage_status: UsageStatus, locale: str = "en") -> str:
    """Build a pre-formatted warning message for when usage is approaching the limit."""
    if not usage_status.limits:
        return _t("messages.limit_warning", locale, remaining=0)

    # Pick the limit closest to being exceeded (highest usage ratio)
    closest = max(
        usage_status.limits,
        key=lambda e: e.current_count / e.limit if e.limit > 0 else 0,
    )

    remaining = max(0, closest.limit - closest.current_count)
    msg = _t("messages.limit_warning", locale, remaining=remaining)

    detail = _t(
        "messages.limit_detail",
        locale,
        current=closest.current_count,
        limit=closest.limit,
        period=get_period_label(closest.period, locale),
        scope=describe_pattern(closest.pattern, locale),
    )
    msg += " · " + detail

    if closest.reset_at:
        msg += " · " + _format_reset_label(closest.reset_at, locale)

    return msg


def build_usage_limit_messages(limit: int | None, period: UsageLimitPeriod | None) -> LocaleString:
    """Build translated error messages for usage limit exceeded error."""
    if limit is None or period is None:
        return LocaleString(**{locale: _t("messages.limit_exceeded", locale) for locale in _LOCALES})

    return LocaleString(
        **{
            locale: _t("messages.limit_reached", locale, limit=limit, period=get_period_label(period, locale))
            for locale in _LOCALES
        }
    )
