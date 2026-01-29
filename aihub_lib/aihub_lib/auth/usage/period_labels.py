"""Multilingual labels for usage limit periods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aihub_lib.auth.usage.UsageLimitService import UsageLimitPeriod
from aihub_lib.i18n.LocaleString import LocaleString

if TYPE_CHECKING:
    from aihub_lib.auth.usage.UsageLimitService import UsageStatus


PERIOD_LABELS: dict[str, LocaleString] = {
    UsageLimitPeriod.ONE_HOUR: LocaleString(
        en="hour",
        de="Stunde",
        fr="heure",
        it="ora",
    ),
    UsageLimitPeriod.ONE_DAY: LocaleString(
        en="day",
        de="Tag",
        fr="jour",
        it="giorno",
    ),
    UsageLimitPeriod.SEVEN_DAYS: LocaleString(
        en="week",
        de="Woche",
        fr="semaine",
        it="settimana",
    ),
    UsageLimitPeriod.ONE_MONTH: LocaleString(
        en="month",
        de="Monat",
        fr="mois",
        it="mese",
    ),
}


def get_period_label(period: str | None, locale: str = "en") -> str:
    """Get the localized label for a usage period."""
    if period is None:
        return ""
    label = PERIOD_LABELS.get(period)
    if label is None:
        return period
    return label.in_locale(locale) or period


PATTERN_SCOPE_LABELS: dict[str, LocaleString] = {
    ">": LocaleString(en="all agents", de="alle Agenten", fr="tous les agents", it="tutti gli agenti"),
    "*": LocaleString(en="all agents", de="alle Agenten", fr="tous les agents", it="tutti gli agenti"),
}

_PATTERN_PREFIX = "aihub.user.agent."


def describe_pattern(pattern: str, locale: str = "en") -> str:
    """Convert a NATS-style usage limit pattern to a human-readable scope label.

    Examples:
        ``aihub.user.agent.>``          → "all agents"
        ``aihub.user.agent.*.*``        → "all agents"
        ``aihub.user.agent.MyAgent.*``  → "MyAgent agents"
        ``aihub.user.agent.MyAgent.v1`` → "MyAgent/v1"
    """
    suffix = pattern.removeprefix(_PATTERN_PREFIX) if pattern.startswith(_PATTERN_PREFIX) else pattern

    # Check for well-known catch-all patterns
    label = PATTERN_SCOPE_LABELS.get(suffix)
    if label:
        return label.in_locale(locale) or suffix

    parts = suffix.split(".")
    # e.g. ["MyAgent", "*"] or ["*", "*"]
    if all(p in ("*", ">") for p in parts):
        return PATTERN_SCOPE_LABELS[">"].in_locale(locale) or suffix

    # Specific class with wildcard id: "MyAgent.*" → "MyAgent agents"
    if len(parts) == 2 and parts[1] in ("*", ">"):
        return f"{parts[0]}"

    # Fully specific: "MyAgent.v1" → "MyAgent/v1"
    return "/".join(parts)


def build_exceeded_detail(usage_status: UsageStatus) -> dict[str, Any]:
    """Build the 429 response detail dict from a UsageStatus.

    Includes backward-compatible single-limit fields plus a full ``limits`` array
    so that consumers can display all exceeded limits.
    """
    from datetime import datetime, timezone as tz

    import zoneinfo

    error_messages = build_usage_limit_messages(usage_status.limit, usage_status.period)

    reset_at_local = None
    reset_in_seconds = None
    if usage_status.reset_at:
        now = datetime.now(tz.utc)
        delta = usage_status.reset_at - now
        reset_in_seconds = max(0, int(delta.total_seconds()))

        user_tz = zoneinfo.ZoneInfo("Europe/Zurich")
        local_time = usage_status.reset_at.astimezone(user_tz)
        reset_at_local = local_time.strftime("%H:%M")

    return {
        "error": "usage_limit_exceeded",
        "messages": error_messages.model_dump(),
        # Backward-compat single-limit fields
        "current_count": usage_status.current_count,
        "limit": usage_status.limit,
        "period": usage_status.period,
        "reset_at": usage_status.reset_at.isoformat() if usage_status.reset_at else None,
        "reset_at_local": reset_at_local,
        "reset_in_seconds": reset_in_seconds,
        # Full multi-limit array
        "limits": [
            {
                "pattern": ls.pattern,
                "scope": {
                    locale: describe_pattern(ls.pattern, locale) for locale in ("en", "de", "fr", "it")
                },
                "limit": ls.limit,
                "period": ls.period,
                "period_label": {
                    locale: get_period_label(ls.period, locale) for locale in ("en", "de", "fr", "it")
                },
                "current_count": ls.current_count,
                "is_exceeded": ls.is_exceeded,
            }
            for ls in usage_status.limits
        ],
    }


def build_usage_limit_messages(limit: int | None, period: str | None) -> LocaleString:
    """Build translated error messages for usage limit exceeded error."""
    if limit is None or period is None:
        return LocaleString(
            en="Usage limit exceeded",
            de="Nutzungslimit erreicht",
            fr="Limite d'utilisation atteinte",
            it="Limite di utilizzo raggiunto",
        )

    en_period = get_period_label(period, "en")
    de_period = get_period_label(period, "de")
    fr_period = get_period_label(period, "fr")
    it_period = get_period_label(period, "it")

    return LocaleString(
        en=f"Usage limit reached: {limit} agent calls per {en_period}",
        de=f"Nutzungslimit erreicht: {limit} Agentenaufrufe pro {de_period}",
        fr=f"Limite d'utilisation atteinte: {limit} appels d'agent par {fr_period}",
        it=f"Limite di utilizzo raggiunto: {limit} chiamate agente per {it_period}",
    )
