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
    dialog's free answer or a typed reply, is read once more by the model, unless it is only a "yes". The keywords are
    taken as answered, after any second reading, since they are hints for the search and never part of the request.
    """

    reading: Annotated[ExtractionRequestAnswer, Field(description="The reading with the chosen options applied.")]
    correction: Annotated[
        str | None, Field(description="What the user wrote, as the parts to read again; None when nothing was.")
    ]
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
        reading = ExtractionRequestAnswers._with_options(understood, answers).model_copy(update=chosen)
        written = {
            key: text
            for key in ("where", "rows", "columns")
            if (text := ExtractionForm.written(answers.get(key))) is not None
        }
        if not written:
            return cls(reading=reading, correction=None, keywords=chosen)
        parts = ExtractionRequestParts.of(reading, t, keywords).model_copy(update=written)
        return cls(reading=reading, correction="\n".join(parts.lines(t)), keywords=chosen)

    def applied(self, reading: ExtractionRequestAnswer) -> ExtractionRequestAnswer:
        """A second reading with the keywords the user answered."""
        return reading.model_copy(update=self.keywords)

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
    def _with_options(
        understood: ExtractionRequestAnswer, answers: dict[str, dict[str, Any]]
    ) -> ExtractionRequestAnswer:
        update: dict[str, Any] = {}
        if ExtractionForm.dropped(answers.get("where")):
            update["locations"] = []
        if ExtractionForm.dropped(answers.get("rows")):
            update["instructions"] = None
        return understood.model_copy(update=update)
