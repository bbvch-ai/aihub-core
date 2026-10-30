import json
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts

YES_WORDS = frozenset({"yes", "y", "ok", "okay", "ja", "oui", "sì", "si", "go", "go ahead", "weiter"})
_PUNCTUATION = " .!?,;:*_\"'"


class ExtractionRequestAnswers(BaseModel):
    """The user's answer to the request form, applied to the reading it confirms.

    A chosen option needs no model: the first keeps the part, the second drops it. What the user wrote instead, as a
    dialog's free answer or a typed reply, is read once more by the model, unless it is only a "yes".
    """

    reading: Annotated[ExtractionRequestAnswer, Field(description="The reading with the chosen options applied.")]
    correction: Annotated[
        str | None, Field(description="What the user wrote, as the parts to read again; None when nothing was.")
    ]

    @classmethod
    def of(cls, response: str, understood: ExtractionRequestAnswer, t: LocaleHandler) -> Self:
        answers = ExtractionRequestAnswers._dialog_answers(response)
        if answers is None:
            typed = response.strip().strip(_PUNCTUATION).casefold()
            return cls(reading=understood, correction=None if typed in YES_WORDS else response.strip())
        reading = ExtractionRequestAnswers._with_options(understood, answers)
        written = {
            key: str(answer.get("text") or "").strip()
            for key, answer in answers.items()
            if answer.get("type") == "other" and str(answer.get("text") or "").strip()
        }
        if not written:
            return cls(reading=reading, correction=None)
        parts = ExtractionRequestParts.of(reading, t).model_copy(update=written)
        return cls(reading=reading, correction="\n".join(parts.lines(t)))

    @staticmethod
    def _dialog_answers(response: str) -> dict[str, dict[str, Any]] | None:
        """The dialog's answers by question id; None for a typed reply."""
        try:
            answers = json.loads(response)
        except json.JSONDecodeError:
            return None
        if not isinstance(answers, dict) or not all(isinstance(answer, dict) for answer in answers.values()):
            return None
        return answers

    @staticmethod
    def _with_options(
        understood: ExtractionRequestAnswer, answers: dict[str, dict[str, Any]]
    ) -> ExtractionRequestAnswer:
        dropped = {
            key
            for key, answer in answers.items()
            if answer.get("type") == "option" and int(answer.get("option_index") or 0) > 0
        }
        update: dict[str, Any] = {}
        if "where" in dropped:
            update["locations"] = []
        if "rows" in dropped:
            update["instructions"] = None
        return understood.model_copy(update=update)
