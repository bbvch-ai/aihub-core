from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

_JQL_MINUTE = "%Y/%m/%d %H:%M"


class JiraTimestamp:
    """Jira writes timestamps in the API user's time zone (``2026-10-08T10:15:30.000+0200``) and reads JQL dates in
    that zone too, to the minute. Files and the sync cursor keep UTC, so a change of that user's zone or a DST switch
    never rewrites an unchanged issue."""

    @staticmethod
    def to_utc(value: str) -> datetime:
        return datetime.fromisoformat(value).astimezone(UTC)

    @classmethod
    def to_utc_iso(cls, value: str) -> str:
        return cls.to_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def zone_of(account: dict[str, Any]) -> ZoneInfo:
        """The zone Jira reads the account's JQL dates in, from its ``/myself`` answer."""
        return ZoneInfo(account.get("timeZone") or "UTC")

    @staticmethod
    def jql_lower_bound(start: datetime | None, zone: ZoneInfo) -> str | None:
        """The ``updated >=`` value for issues changed since ``start``; None when there is no cursor yet.

        Floored to the minute, so it never starts after ``start``. A local time the clocks pass twice when daylight
        saving ends is moved an hour back, because Jira may read it as the later of the two.
        """
        if start is None:
            return None
        aware = start if start.tzinfo else start.replace(tzinfo=UTC)
        local = aware.astimezone(zone).replace(tzinfo=None, second=0, microsecond=0)
        if local.replace(tzinfo=zone, fold=0).utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
            local -= timedelta(hours=1)
        return local.strftime(_JQL_MINUTE)
