from __future__ import annotations

import zoneinfo
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, RoleUsageLimitStatus, UsageLimitPeriod, UsageStatus
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString

_LOCALES = LocaleHandler.LOCALE_WHITE_LIST
_DEFAULT_TIMEZONE = zoneinfo.ZoneInfo("Europe/Zurich")

_RESOURCE_PATH_PREFIX = "aihub.user."
_RESOURCE_TYPE_SEGMENT_INDEX = 2


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


def _extract_resource_parts(pattern: str) -> tuple[str, str]:
    """Extract the resource suffix and derive the i18n scope key from the pattern.

    Patterns follow ``aihub.user.<resource_type>.<class>.<id>``.
    The scope key is derived as ``all_<resource_type>s`` (e.g. ``all_agents``),
    so new resource types get a scope key automatically without a manual mapping.
    """
    segments = pattern.split(".")
    if len(segments) > _RESOURCE_TYPE_SEGMENT_INDEX and pattern.startswith(_RESOURCE_PATH_PREFIX):
        resource_type = segments[_RESOURCE_TYPE_SEGMENT_INDEX]
        suffix = ".".join(segments[_RESOURCE_TYPE_SEGMENT_INDEX + 1 :])
        return suffix, f"all_{resource_type}s"
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
    suffix, scope_key = _extract_resource_parts(pattern)

    if not suffix or suffix in (">", "*") or all(segment in ("*", ">") for segment in suffix.split(".")):
        return _t(f"scope.{scope_key}", locale)

    parts = suffix.split(".")
    if len(parts) == 2 and parts[1] in ("*", ">"):
        return parts[0]

    return "/".join(parts)


_WEEKDAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _format_reset_label(reset_at: datetime, locale: str) -> str:
    """Build a localized reset label that adapts to how far away the reset is.

    - Same day  → "Resets at 11:35"
    - Tomorrow  → "Resets tomorrow at 11:35"
    - Within 7 days → "Resets on Wednesday at 11:35"
    - Further   → "Resets on 15.02.2025 at 11:35"
    """
    local_reset = reset_at.astimezone(_DEFAULT_TIMEZONE)
    local_now = datetime.now(_DEFAULT_TIMEZONE)
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


class LimitDetail(RoleUsageLimit):
    """One limit entry in the exceeded-detail response, extending the base limit with presentation fields."""

    scope: Annotated[dict[str, str], Field(description="Localized scope labels keyed by locale")]
    period_label: Annotated[dict[str, str], Field(description="Localized period labels keyed by locale")]
    current_count: Annotated[int, Field(ge=0, description="Number of calls made in the current period")]
    is_exceeded: Annotated[bool, Field(description="Whether the current count has reached or exceeded the limit")]


class ExceededDetail(BaseModel):
    """Structured 429 response body for usage limit exceeded errors."""

    error: Annotated[str, Field(description="Machine-readable error code")] = "usage_limit_exceeded"
    message: Annotated[str, Field(description="Pre-formatted, locale-aware display message")]
    messages: Annotated[dict[str, str], Field(description="Legacy per-locale error messages")]
    current_count: Annotated[int | None, Field(description="Current call count of the most restrictive exceeded limit")]
    limit: Annotated[int | None, Field(description="Maximum allowed calls of the most restrictive exceeded limit")]
    period: Annotated[UsageLimitPeriod | None, Field(description="Time window of the most restrictive exceeded limit")]
    reset_at: Annotated[str | None, Field(description="ISO 8601 UTC reset timestamp")]
    reset_at_local: Annotated[str | None, Field(description="Local time (HH:MM) of reset")]
    reset_in_seconds: Annotated[int | None, Field(description="Seconds until counter resets")]
    limits: Annotated[list[LimitDetail], Field(description="All evaluated limits with their current status")]


def _build_limit_detail(limit_status: RoleUsageLimitStatus) -> LimitDetail:
    """Build a single limit detail entry with all locale variants."""
    return LimitDetail(
        pattern=limit_status.pattern,
        scope={locale: describe_pattern(limit_status.pattern, locale) for locale in _LOCALES},
        limit=limit_status.limit,
        period=limit_status.period,
        period_label={locale: get_period_label(limit_status.period, locale) for locale in _LOCALES},
        current_count=limit_status.current_count,
        is_exceeded=limit_status.is_exceeded,
    )


def _compute_reset_fields(reset_at: datetime) -> tuple[str, int]:
    """Derive local time string and seconds-until-reset from a UTC reset timestamp."""
    local_time = reset_at.astimezone(_DEFAULT_TIMEZONE)
    reset_at_local = local_time.strftime("%H:%M")

    delta = reset_at - datetime.now(UTC)
    reset_in_seconds = max(0, int(delta.total_seconds()))

    return reset_at_local, reset_in_seconds


def build_exceeded_detail(usage_status: UsageStatus, locale: str = "en") -> ExceededDetail:
    """Build the 429 response detail from a UsageStatus.

    The ``message`` field contains a single pre-formatted, locale-aware string
    ready for display. The ``messages`` dict and ``limits`` array are kept for
    backward compatibility.
    """
    error_messages = build_usage_limit_messages(usage_status.limit, usage_status.period)

    reset_at_local = None
    reset_in_seconds = None
    if usage_status.reset_at:
        reset_at_local, reset_in_seconds = _compute_reset_fields(usage_status.reset_at)

    reset_label = _format_reset_label(usage_status.reset_at, locale) if usage_status.reset_at else None
    message = _build_display_message(usage_status, locale, reset_label)

    return ExceededDetail(
        message=message,
        messages=error_messages.model_dump(),
        current_count=usage_status.current_count,
        limit=usage_status.limit,
        period=usage_status.period,
        reset_at=usage_status.reset_at.isoformat() if usage_status.reset_at else None,
        reset_at_local=reset_at_local,
        reset_in_seconds=reset_in_seconds,
        limits=[_build_limit_detail(limit_status) for limit_status in usage_status.limits],
    )


def _build_display_message(usage_status: UsageStatus, locale: str, reset_label: str | None) -> str:
    """Build a single ready-to-display message in the user's locale."""
    exceeded_limits = [limit_status for limit_status in usage_status.limits if limit_status.is_exceeded]

    if exceeded_limits:
        detail_lines = [
            _t(
                "messages.limit_detail",
                locale,
                current=limit_status.current_count,
                limit=limit_status.limit,
                period=get_period_label(limit_status.period, locale),
                scope=describe_pattern(limit_status.pattern, locale),
            )
            for limit_status in exceeded_limits
        ]
        message = _t("messages.limit_exceeded", locale) + ": " + " · ".join(detail_lines)
    else:
        message = _t("messages.limit_exceeded", locale)

    if reset_label:
        message += " · " + reset_label

    return message


def build_warning_message(usage_status: UsageStatus, locale: str = "en") -> str:
    """Build a pre-formatted warning message for when usage is approaching the limit."""
    if not usage_status.limits:
        return _t("messages.limit_warning", locale, remaining=0)

    closest_to_exceeded = max(
        usage_status.limits,
        key=lambda limit_status: limit_status.current_count / limit_status.limit if limit_status.limit > 0 else 0,
    )

    remaining = max(0, closest_to_exceeded.limit - closest_to_exceeded.current_count)
    message = _t("messages.limit_warning", locale, remaining=remaining)

    detail = _t(
        "messages.limit_detail",
        locale,
        current=closest_to_exceeded.current_count,
        limit=closest_to_exceeded.limit,
        period=get_period_label(closest_to_exceeded.period, locale),
        scope=describe_pattern(closest_to_exceeded.pattern, locale),
    )
    message += " · " + detail

    if closest_to_exceeded.reset_at:
        message += " · " + _format_reset_label(closest_to_exceeded.reset_at, locale)

    return message


_USAGE_WARNING_THRESHOLD_PERCENT = 80

_SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
    "Content-Encoding": "identity",
}


def build_streaming_response_headers(usage_status: UsageStatus, locale: str = "en") -> dict[str, str]:
    """Build SSE response headers, adding usage warning headers when usage reaches 80%+."""
    headers = dict(_SSE_HEADERS)

    if usage_status.limit is None or usage_status.current_count is None:
        return headers

    usage_percentage = (usage_status.current_count / usage_status.limit) * 100
    if usage_percentage < _USAGE_WARNING_THRESHOLD_PERCENT:
        return headers

    remaining = usage_status.limit - usage_status.current_count
    headers["X-Usage-Warning"] = "true"
    headers["X-Usage-Warning-Message"] = build_warning_message(usage_status, locale=locale)
    headers["X-Usage-Current"] = str(usage_status.current_count)
    headers["X-Usage-Limit"] = str(usage_status.limit)
    headers["X-Usage-Remaining"] = str(remaining)
    headers["X-Usage-Period"] = usage_status.period or ""
    return headers


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
