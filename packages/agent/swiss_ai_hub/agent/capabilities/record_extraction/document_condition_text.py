from swiss_ai_hub.core.generative_ai import DocumentAttributeCondition, DocumentMetadataFilter, PathDateRange
from swiss_ai_hub.core.i18n import LocaleHandler

_PERIOD = "agent.record_extraction.period"
_METADATA = "agent.record_extraction.metadata"


class DocumentConditionText:
    """The document condition as the user and the judge read it: the user's words, then the period put into words by
    code, since the model writes the period as dates and never into the condition."""

    @staticmethod
    def of(
        condition: str | None,
        date_range: PathDateRange | None,
        t: LocaleHandler,
        metadata_filter: DocumentMetadataFilter | None = None,
    ) -> str | None:
        """`metadata_filter` is shown only where the user confirms the request: the judge reads the condition in the
        user's words, which already name what the filter compares."""
        period = DocumentConditionText.period(date_range, t) if date_range is not None else None
        metadata = DocumentConditionText.metadata(metadata_filter, t) if metadata_filter is not None else None
        return "; ".join(part for part in (condition, period, metadata) if part) or None

    @staticmethod
    def metadata(metadata_filter: DocumentMetadataFilter, t: LocaleHandler) -> str:
        """The types and recorded values the filter compares, in words."""
        types = [t(f"{_METADATA}.types", types=", ".join(metadata_filter.types))] if metadata_filter.types else []
        conditions = [DocumentConditionText._condition(condition, t) for condition in metadata_filter.conditions]
        return ", ".join([*types, *conditions])

    @staticmethod
    def _condition(condition: DocumentAttributeCondition, t: LocaleHandler) -> str:
        attribute = condition.attribute.value.removeprefix("document_").replace("_", " ")
        if condition.contains is not None:
            return t(f"{_METADATA}.contains", attribute=attribute, text=condition.contains)
        if condition.at_least is not None and condition.at_most is not None:
            return t(f"{_METADATA}.between", attribute=attribute, low=condition.at_least, high=condition.at_most)
        if condition.at_least is not None:
            return t(f"{_METADATA}.at_least", attribute=attribute, low=condition.at_least)
        return t(f"{_METADATA}.at_most", attribute=attribute, high=condition.at_most)

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
