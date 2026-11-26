from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import ExtractionForm

_KEYWORD_FIELDS = {"exact": "document_terms", "semantic": "document_kind"}
_DROPPABLE = ("where", "documents", "rows")


class ExtractionRequestAnswers(BaseModel):
    """The user's answer to the request form, applied to the reading it confirms.

    A chosen option needs no model: the first keeps the part, the second drops it, and so does a typed line naming that
    option for a part the request named, such as "Document Condition: Every document". What the user wrote instead, as
    a dialog's free answer or a typed reply, is read once more by the model, unless it is only a "yes". The dropped
    parts and the keywords are applied again after that second reading: the model reads the whole conversation, and may
    bring back from the first message a part the user dropped. When the dialog kept the Location as shown, the second
    reading also loses the date folders that repeat the period (`keeps_location`), so a year folder the first reading
    dropped cannot come back, while a file or a folder path written into another part still counts.
    """

    reading: Annotated[ExtractionRequestAnswer, Field(description="The reading with the chosen options applied.")]
    correction: Annotated[
        str | None, Field(description="What the user wrote, as the parts to read again; None when nothing was.")
    ]
    dropped: Annotated[
        dict[str, Any], Field(description="The parts the user dropped, as the reading fields they clear.")
    ] = {}
    keeps_location: Annotated[
        bool,
        Field(description="Whether the dialog kept the Location as shown: it wrote nothing there, dropped nothing."),
    ] = False
    keywords: Annotated[
        dict[str, str | None], Field(description="The keyword answers by reading field, applied last.")
    ] = {}
    period: Annotated[
        tuple[str | None, str | None],
        Field(description="The period understood before; a dropped period is cleared again only when it comes back."),
    ] = (None, None)

    @classmethod
    def of(cls, response: str, understood: ExtractionRequestAnswer, t: LocaleHandler, keywords: bool = False) -> Self:
        answers = ExtractionForm.dialog_answers(response)
        period = (understood.period_start, understood.period_end)
        if answers is None:
            correction = None if ExtractionForm.is_yes(response) else response.strip()
            named = ExtractionRequestParts.named(understood)
            dropped = ExtractionRequestAnswers._cleared(
                {key for key in _DROPPABLE if named[key] and ExtractionForm.typed_dropped(response, key, t)}
            )
            reading = understood.model_copy(update=dropped)
            return cls(reading=reading, correction=correction, dropped=dropped, period=period)
        chosen = ExtractionRequestAnswers._keywords(understood, answers) if keywords else {}
        dropped = ExtractionRequestAnswers._dropped(answers)
        reading = understood.model_copy(update={**dropped, **chosen})
        written = {
            key: text
            for key in ("where", "documents", "rows", "columns")
            if (text := ExtractionForm.written(answers.get(key))) is not None
        }
        if not written:
            return cls(reading=reading, correction=None, dropped=dropped, keywords=chosen, period=period)
        parts = ExtractionRequestParts.of(reading, t, keywords).model_copy(update=written)
        correction = "\n".join(parts.lines(t))
        keeps_location = "where" not in written and "locations" not in dropped
        return cls(
            reading=reading,
            correction=correction,
            dropped=dropped,
            keeps_location=keeps_location,
            keywords=chosen,
            period=period,
        )

    def applied(self, reading: ExtractionRequestAnswer) -> ExtractionRequestAnswer:
        """A second reading with the parts the user dropped and the keywords the user answered. A dropped period is
        cleared only when the second reading brought back the one understood, not a period the user wrote elsewhere."""
        update = {**self.dropped, **self.keywords}
        if (reading.period_start, reading.period_end) != self.period:
            update = {field: value for field, value in update.items() if field not in ("period_start", "period_end")}
        return reading.model_copy(update=update)

    @staticmethod
    def _keywords(understood: ExtractionRequestAnswer, answers: dict[str, dict[str, Any]]) -> dict[str, str | None]:
        """Each keyword as answered: kept, dropped ("None"), or as written."""
        chosen: dict[str, str | None] = {}
        for key, field in _KEYWORD_FIELDS.items():
            answer = answers.get(key)
            written = ExtractionForm.written(answer)
            if written is not None:
                chosen[field] = written
            elif ExtractionForm.dropped(answer):
                chosen[field] = None
            else:
                chosen[field] = getattr(understood, field)
        return chosen

    @staticmethod
    def _dropped(answers: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Each part whose second option the user chose, as the reading field it clears."""
        return ExtractionRequestAnswers._cleared(
            {key for key in _DROPPABLE if ExtractionForm.dropped(answers.get(key))}
        )

    @staticmethod
    def _cleared(keys: set[str]) -> dict[str, Any]:
        """The reading fields the dropped parts clear; every document drops the period too."""
        cleared: dict[str, Any] = {}
        if "where" in keys:
            cleared["locations"] = []
        if "documents" in keys:
            cleared.update(document_condition=None, period_start=None, period_end=None)
        if "rows" in keys:
            cleared["instructions"] = None
        return cleared
