from datetime import UTC, datetime


class JiraTimestamp:
    """Jira writes timestamps in the API user's time zone (``2026-10-08T10:15:30.000+0200``); files carry them in UTC,
    so a change of that user's time zone or a DST switch never rewrites an unchanged issue."""

    @staticmethod
    def to_utc_iso(value: str) -> str:
        return datetime.fromisoformat(value).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
