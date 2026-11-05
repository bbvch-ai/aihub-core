import json
from typing import Any

from swiss_ai_hub.core.events.agent import HumanInTheLoopChoiceOption, HumanInTheLoopChoiceQuestion
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form_part import ExtractionFormPart

FORM = "agent.record_extraction.form"
# OpenWebUI's dialog cuts longer texts; cutting here keeps the end visible as an ellipsis.
QUESTION_LENGTH = 500
DESCRIPTION_LENGTH = 240
YES_WORDS = frozenset({"yes", "y", "ok", "okay", "ja", "oui", "sì", "si", "go", "go ahead", "weiter"})
NO_WORDS = frozenset({"no", "n", "nein", "non", "cancel", "stop", "abbrechen", "annuler", "annulla"})
_PUNCTUATION = " .!?,;:*_\"'"


class ExtractionForm:
    """The request form an extraction asks before any document is read, as dialog questions and as text.

    Each part is a choice question whose first option keeps it as understood and whose second, when the part can be
    dropped, drops it; a free answer corrects it. A part the request did not name offers only what applies without it.
    Notices open the first question and each part's hint closes its own, since a dialog shows only the questions; the
    end, where a folder list stands, is what a long question loses. The text carries the same wording for clients
    without a dialog.
    """

    @staticmethod
    def questions(
        parts: list[ExtractionFormPart], notices: list[str], t: LocaleHandler
    ) -> list[HumanInTheLoopChoiceQuestion]:
        return [ExtractionForm._question(part, notices if index == 0 else [], t) for index, part in enumerate(parts)]

    @staticmethod
    def text(parts: list[ExtractionFormPart], notices: list[str], t: LocaleHandler) -> str:
        """Notices first, then the parts as understood, then what each part may say."""
        understood = [f"- {ExtractionForm.line(part.key, part.value, t)}" for part in parts]
        guidance = [f"- **{t(f'{FORM}.{part.key}.header')}:** {part.hint}" for part in parts]
        return "\n".join(
            [*(f"{notice}\n" for notice in notices), t(f"{FORM}.intro"), "", *understood, "", t(f"{FORM}.reply_hint")]
            + guidance
        )

    @staticmethod
    def line(key: str, value: str, t: LocaleHandler) -> str:
        return t(f"{FORM}.{key}.line", value=value)

    @staticmethod
    def dialog_answers(response: str) -> dict[str, dict[str, Any]] | None:
        """The dialog's answers by question id; None for a typed reply."""
        try:
            answers = json.loads(response)
        except json.JSONDecodeError:
            return None
        if not isinstance(answers, dict) or not all(isinstance(answer, dict) for answer in answers.values()):
            return None
        return answers

    @staticmethod
    def dropped(answer: dict[str, Any] | None) -> bool:
        """Whether the answer chose an option after the first: anything, every row, none."""
        return bool(answer) and answer.get("type") == "option" and int(answer.get("option_index") or 0) > 0

    @staticmethod
    def written(answer: dict[str, Any] | None) -> str | None:
        """What the user wrote instead of choosing; None when they chose."""
        if not answer or answer.get("type") != "other":
            return None
        return str(answer.get("text") or "").strip() or None

    @staticmethod
    def is_yes(reply: str) -> bool:
        return ExtractionForm._plain(reply) in YES_WORDS

    @staticmethod
    def is_no(reply: str) -> bool:
        return ExtractionForm._plain(reply) in NO_WORDS

    @staticmethod
    def _plain(reply: str) -> str:
        return reply.strip().strip(_PUNCTUATION).casefold()

    @staticmethod
    def _question(part: ExtractionFormPart, notices: list[str], t: LocaleHandler) -> HumanInTheLoopChoiceQuestion:
        understood = HumanInTheLoopChoiceOption(
            label=t(f"{FORM}.as_understood"), description=ExtractionForm._clip(part.value, DESCRIPTION_LENGTH)
        )
        anything = HumanInTheLoopChoiceOption(
            label=t(f"{FORM}.{part.key}.anything"), description=t(f"{FORM}.{part.key}.anything_description")
        )
        if part.named:
            options = [understood, anything] if part.droppable else [understood]
        else:
            options = [anything]
        text = " ".join([*notices, t(f"{FORM}.{part.key}.question", value=part.value), part.hint])
        return HumanInTheLoopChoiceQuestion(
            id=part.key,
            header=t(f"{FORM}.{part.key}.header"),
            question=ExtractionForm._clip(text, QUESTION_LENGTH),
            options=options,
            allow_other=True,
        )

    @staticmethod
    def _clip(text: str, length: int) -> str:
        return text if len(text) <= length else f"{text[: length - 1]}…"
