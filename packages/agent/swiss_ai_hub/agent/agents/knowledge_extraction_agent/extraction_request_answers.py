from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import ExtractionForm

_KEYWORD_FIELDS = {"exact": "document_terms", "semantic": "document_kind"}


class ExtractionRequestAnswers(BaseModel):
    """The user's answer to the request form, applied to the reading it confirms.

    A chosen option needs no model: the first keeps the part, the second drops it. What the user wrote instead, as a
    dialog's free answer or a typed reply, is read once more by the model, unless it is only a "yes". The dropped parts
    and the keywords are applied again after that second reading: the model reads the whole conversation, and may bring
    back from the first message a part the user dropped.
    """

    reading: Annotated[ExtractionRequestAnswer, Field(description="The reading with the chosen options applied.")]
    correction: Annotated[
        str | None, Field(description="What the user wrote, as the parts to read again; None when nothing was.")
    ]
    dropped: Annotated[
        dict[str, Any], Field(description="The parts the user dropped, as the reading fields they clear.")
    ] = {}
    keywords: Annotated[
        dict[str, str | None], Field(description="The keyword answers by reading field, applied last.")
    ] = {}

    @classmethod
    def of(cls, response: str, understood: ExtractionRequestAnswer, t: LocaleHandler, keywords: bool = False) -> Self:
        answers = ExtractionForm.dialog_answers(response)
        if answers is None:
            correction = None if ExtractionForm.is_yes(response) else response.strip()
            return cls(reading=understood, correction=correction)
        chosen = ExtractionRequestAnswers._keywords(understood, answers) if keywords else {}
        dropped = ExtractionRequestAnswers._dropped(answers)
        reading = understood.model_copy(update={**dropped, **chosen})
        written = {
            key: text
            for key in ("where", "documents", "rows", "columns")
            if (text := ExtractionForm.written(answers.get(key))) is not None
        }
        if not written:
            return cls(reading=reading, correction=None, dropped=dropped, keywords=chosen)
        parts = ExtractionRequestParts.of(reading, t, keywords).model_copy(update=written)
        return cls(reading=reading, correction="\n".join(parts.lines(t)), dropped=dropped, keywords=chosen)

    def applied(self, reading: ExtractionRequestAnswer) -> ExtractionRequestAnswer:
        """A second reading with the parts the user dropped and the keywords the user answered."""
        return reading.model_copy(update={**self.dropped, **self.keywords})

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
        cleared: dict[str, Any] = {}
        if ExtractionForm.dropped(answers.get("where")):
            cleared["locations"] = []
        if ExtractionForm.dropped(answers.get("documents")):
            cleared["document_condition"] = None
        if ExtractionForm.dropped(answers.get("rows")):
            cleared["instructions"] = None
        return cleared
