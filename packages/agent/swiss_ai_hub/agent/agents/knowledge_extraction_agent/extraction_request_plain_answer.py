import logging
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria, KnowledgeDocumentSelection, PathDateRange
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation
from swiss_ai_hub.agent.capabilities.record_extraction.document_condition_text import DocumentConditionText

logger = logging.getLogger(__name__)


class ExtractionRequestPlainAnswer(BaseModel):
    """A chat message read as a table request without the search terms: what the reading falls back to when a model
    loops in a term list until its output is cut, since the terms only order the documents and pick the sample."""

    is_table_request: Annotated[
        bool,
        Field(
            description="True when the message asks for records collected from the documents, a question the "
            "documents answer included, or confirms the sample of one; false for anything else, such as a greeting or "
            "a question about the agent."
        ),
    ]
    confirms_sample: Annotated[
        bool,
        Field(
            description="True only when a sample awaits confirmation and the message agrees to extract all of it, "
            "e.g. 'yes', 'go on', 'ja'; false for a new or changed request."
        ),
    ]
    locations: Annotated[
        list[RequestedLocation],
        Field(description="The collections, folders or files the user named; empty when the whole scope is meant."),
    ]
    fields: Annotated[
        str,
        Field(
            description="The table's columns in the user's words: the value of each record, never the result of a "
            "calculation over the records."
        ),
    ]
    document_condition: Annotated[
        str | None,
        Field(
            description="Which documents count, in the user's words, other than the period that dates them: a "
            "condition the whole document meets or fails, such as its supplier or party, its number, its status or "
            "version, e.g. 'contracts with Hooli', 'only signed versions'. The period goes into period_start and "
            "period_end. Null when every document at the locations counts, or when the rows carry the value "
            "themselves."
        ),
    ] = None
    period_start: Annotated[
        str | None,
        Field(
            description="The first day of the period that dates the wanted documents, as YYYY-MM-DD, e.g. "
            "'2018-10-01' for Q4 2018; null when the request names no such period or it has no start."
        ),
    ] = None
    period_end: Annotated[
        str | None,
        Field(
            description="The last day of that period, as YYYY-MM-DD, e.g. '2018-12-31' for Q4 2018; null when the "
            "request names no such period or it has no end."
        ),
    ] = None
    instructions: Annotated[
        str | None,
        Field(
            description="Which rows to keep, in the user's words: the kind of row or a condition on a row's values, "
            "e.g. 'only hardware positions', also a supplier, party or date the rows carry themselves, as on a "
            "statement. A condition on the whole document goes into document_condition. Null when every row is "
            "wanted."
        ),
    ]
    calculation: Annotated[
        str | None,
        Field(
            description="The sum, average, count, maximum or comparison the user asked for over the rows, in the "
            "user's words; null when none. The agent lists the values and does not calculate."
        ),
    ]
    document_kind: Annotated[
        str | None,
        Field(
            description="The kind of document the wanted rows stand in, in a few words, e.g. 'supplier invoice with "
            "line items'; no amounts, dates or thresholds. Null when the request does not say."
        ),
    ]

    @property
    def path_date_range(self) -> PathDateRange | None:
        """The period as code reads it; a reading that went through `with_readable_period` always has one or none."""
        return PathDateRange.written(self.period_start, self.period_end)

    @property
    def selection(self) -> KnowledgeDocumentSelection:
        """The named places, or the whole scope when the user named none, dated within the period."""
        criteria = [location.as_criteria() for location in self.locations if location.is_place]
        return KnowledgeDocumentSelection(
            any_of=criteria or [KnowledgeDocumentCriteria()], path_date_range=self.path_date_range
        )

    def without_period_folders(self, message: Annotated[str, "What the user wrote, every turn of it"]) -> Self:
        """The locations without the date folders that only repeat the period (`RequestedLocation`), for the first
        reading of a request only: a Location the user typed into the form is the user's own. A location that becomes
        every document makes the whole scope the place, so a widened list never reads fewer documents."""
        period = self.path_date_range
        if period is None or not self.locations:
            return self
        widened = [location.without_period_folders(period, message) for location in self.locations]
        if widened == self.locations:
            return self
        unique = {(location.collection, location.path_glob, location.path_regex): location for location in widened}
        locations = [] if any(location.is_everywhere for location in widened) else list(unique.values())
        logger.info(
            "[knowledge-extraction] locations %s widened to %s: their date folders only repeat the period",
            [location.describe() for location in self.locations],
            [location.describe() for location in locations],
        )
        return self.model_copy(update={"locations": locations})

    def with_readable_period(self, t: LocaleHandler) -> Self:
        """The period read once, as ISO days. One no code can read stays in the document condition in the model's
        words, so the form and the judge still see it, and narrows no path."""
        try:
            date_range = self.path_date_range
        except ValueError:
            logger.warning(
                "[knowledge-extraction] unreadable period %r to %r, kept in the document condition",
                self.period_start,
                self.period_end,
            )
            words = DocumentConditionText.period_words(self.period_start, self.period_end, t)
            condition = "; ".join(part for part in (self.document_condition, words) if part) or None
            return self.model_copy(update={"document_condition": condition, "period_start": None, "period_end": None})
        start = date_range.start if date_range else None
        end = date_range.end if date_range else None
        return self.model_copy(
            update={
                "period_start": start.isoformat() if start else None,
                "period_end": end.isoformat() if end else None,
            }
        )
