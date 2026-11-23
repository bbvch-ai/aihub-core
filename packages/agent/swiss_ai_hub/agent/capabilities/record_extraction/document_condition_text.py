from swiss_ai_hub.core.generative_ai import PathDateRange
from swiss_ai_hub.core.i18n import LocaleHandler

_PERIOD = "agent.record_extraction.period"


class DocumentConditionText:
    """The document condition as the user and the judge read it: the user's words, then the period put into words by
    code, since the model writes the period as dates and never into the condition."""

    @staticmethod
    def of(condition: str | None, date_range: PathDateRange | None, t: LocaleHandler) -> str | None:
        period = DocumentConditionText.period(date_range, t) if date_range is not None else None
        return "; ".join(part for part in (condition, period) if part) or None

    @staticmethod
    def period(date_range: PathDateRange, t: LocaleHandler) -> str:
        start = date_range.start.isoformat() if date_range.start else None
        end = date_range.end.isoformat() if date_range.end else None
        return DocumentConditionText.period_words(start, end, t)

    @staticmethod
    def period_words(start: str | None, end: str | None, t: LocaleHandler) -> str:
        """The period in words, whatever its bounds say, so a period no code could read is still shown as written."""
        if start and end:
            return t(f"{_PERIOD}.between", start=start, end=end)
        if start:
            return t(f"{_PERIOD}.from", start=start)
        if end:
            return t(f"{_PERIOD}.until", end=end)
        return ""
