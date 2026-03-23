from __future__ import annotations

import zoneinfo
from datetime import UTC, datetime

from swiss_ai_hub.core.auth.usage.access_rule_describer import AccessRuleDescriber
from swiss_ai_hub.core.auth.usage.models.exceeded_detail import ExceededDetail
from swiss_ai_hub.core.auth.usage.models.limit_detail import LimitDetail
from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimitStatus, UsageStatus
from swiss_ai_hub.core.auth.usage.usage_limit_settings import UsageLimitSettings
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

_LOCALES = LocaleHandler.LOCALE_WHITE_LIST
_DEFAULT_TIMEZONE = zoneinfo.ZoneInfo("Europe/Zurich")
_WEEKDAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class UsageLimitMessages:
    """Builds localized messages and structured detail objects for usage limits."""

    @staticmethod
    def build_exceeded_detail(usage_status: UsageStatus, locale: str = LocaleHandler.DEFAULT_LOCALE) -> ExceededDetail:
        """Build the 429 response detail from a UsageStatus.

        The ``message`` field contains a single pre-formatted, locale-aware string
        ready for display.
        """
        reset_at_local = None
        reset_in_seconds = None
        if usage_status.reset_at:
            reset_at_local, reset_in_seconds = UsageLimitMessages._compute_reset_fields(usage_status.reset_at)

        reset_label = (
            UsageLimitMessages._format_reset_label(usage_status.reset_at, locale) if usage_status.reset_at else None
        )
        message = UsageLimitMessages._build_display_message(usage_status, locale, reset_label)

        limits = [UsageLimitMessages._build_limit_detail(limit_status) for limit_status in usage_status.limits]

        return ExceededDetail(
            message=message,
            current_count=usage_status.current_count,
            limit=usage_status.limit,
            period=usage_status.period,
            reset_at=usage_status.reset_at.isoformat() if usage_status.reset_at else None,
            reset_at_local=reset_at_local,
            reset_in_seconds=reset_in_seconds,
            limits=limits,
        )

    @staticmethod
    def build_warning_message(usage_status: UsageStatus, locale: str = LocaleHandler.DEFAULT_LOCALE) -> str:
        """Build a pre-formatted warning message for when usage is approaching the limit."""
        t = LocaleHandler(locale)
        if not usage_status.limits:
            return t("lib.usage.messages.limit_warning", remaining=0)

        closest_to_exceeded = max(
            usage_status.limits,
            key=lambda limit_status: limit_status.current_count / limit_status.limit if limit_status.limit > 0 else 0,
        )

        remaining = max(0, closest_to_exceeded.limit - closest_to_exceeded.current_count)
        message = t("lib.usage.messages.limit_warning", remaining=remaining)

        detail = t(
            "lib.usage.messages.limit_detail",
            current=closest_to_exceeded.current_count,
            limit=closest_to_exceeded.limit,
            period=AccessRuleDescriber.get_period_label(closest_to_exceeded.period, locale),
            scope=AccessRuleDescriber.describe_pattern(closest_to_exceeded.pattern, locale),
        )
        message += " · " + detail

        if closest_to_exceeded.reset_at:
            message += " · " + UsageLimitMessages._format_reset_label(closest_to_exceeded.reset_at, locale)

        return message

    @staticmethod
    def build_usage_warning_headers(
        usage_status: UsageStatus, locale: str = LocaleHandler.DEFAULT_LOCALE
    ) -> dict[str, str]:
        """Build usage warning headers when usage reaches the configured threshold. Returns empty dict if below."""
        if usage_status.limit is None or usage_status.current_count is None:
            return {}

        threshold = UsageLimitSettings().WARNING_THRESHOLD_PERCENT
        usage_percentage = (usage_status.current_count / usage_status.limit) * 100
        if usage_percentage < threshold:
            return {}

        remaining = usage_status.limit - usage_status.current_count
        return {
            "X-Usage-Warning": "true",
            "X-Usage-Warning-Message": UsageLimitMessages.build_warning_message(usage_status, locale=locale),
            "X-Usage-Current": str(usage_status.current_count),
            "X-Usage-Limit": str(usage_status.limit),
            "X-Usage-Remaining": str(remaining),
            "X-Usage-Period": usage_status.period.value if usage_status.period else "",
        }

    @staticmethod
    def _build_limit_detail(limit_status: RoleUsageLimitStatus) -> LimitDetail:
        """Build a single limit detail entry with all locale variants."""
        return LimitDetail(
            pattern=limit_status.pattern,
            scope={locale: AccessRuleDescriber.describe_pattern(limit_status.pattern, locale) for locale in _LOCALES},
            limit=limit_status.limit,
            period=limit_status.period,
            period_label={
                locale: AccessRuleDescriber.get_period_label(limit_status.period, locale) for locale in _LOCALES
            },
            current_count=limit_status.current_count,
            is_exceeded=limit_status.is_exceeded,
        )

    @staticmethod
    def _format_reset_label(reset_at: datetime, locale: str, timezone: zoneinfo.ZoneInfo = _DEFAULT_TIMEZONE) -> str:
        """Build a localized reset label that adapts to how far away the reset is."""
        t = LocaleHandler(locale)
        local_reset = reset_at.astimezone(timezone)
        local_now = datetime.now(timezone)
        time_str = local_reset.strftime("%H:%M")

        days_until = (local_reset.date() - local_now.date()).days

        if days_until <= 0:
            return t("lib.usage.messages.resets_at", time=time_str)
        if days_until == 1:
            return t("lib.usage.messages.resets_tomorrow_at", time=time_str)
        if days_until <= 6:
            weekday_key = _WEEKDAY_KEYS[local_reset.weekday()]
            weekday_name = t(f"lib.usage.weekdays.{weekday_key}")
            return t("lib.usage.messages.resets_on_weekday_at", weekday=weekday_name, time=time_str)

        date_str = local_reset.strftime("%d.%m.%Y")
        return t("lib.usage.messages.resets_on_date_at", date=date_str, time=time_str)

    @staticmethod
    def _compute_reset_fields(reset_at: datetime, timezone: zoneinfo.ZoneInfo = _DEFAULT_TIMEZONE) -> tuple[str, int]:
        """Derive local time string and seconds-until-reset from a reset timestamp."""
        local_time = reset_at.astimezone(timezone)
        reset_at_local = local_time.strftime("%H:%M")

        delta = reset_at - datetime.now(UTC)
        reset_in_seconds = max(0, int(delta.total_seconds()))

        return reset_at_local, reset_in_seconds

    @staticmethod
    def _build_display_message(usage_status: UsageStatus, locale: str, reset_label: str | None) -> str:
        """Build a single ready-to-display message in the user's locale."""
        t = LocaleHandler(locale)
        exceeded_limits = [limit_status for limit_status in usage_status.limits if limit_status.is_exceeded]

        if exceeded_limits:
            detail_lines = [
                t(
                    "lib.usage.messages.limit_detail",
                    current=limit_status.current_count,
                    limit=limit_status.limit,
                    period=AccessRuleDescriber.get_period_label(limit_status.period, locale),
                    scope=AccessRuleDescriber.describe_pattern(limit_status.pattern, locale),
                )
                for limit_status in exceeded_limits
            ]
            message = t("lib.usage.messages.limit_exceeded") + ": " + " · ".join(detail_lines)
        else:
            message = t("lib.usage.messages.limit_exceeded")

        if reset_label:
            message += " · " + reset_label

        return message
