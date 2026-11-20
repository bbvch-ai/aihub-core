import re
from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome

_AMOUNT_TOLERANCE = 0.005


class AttributeComparison:
    """Compares one stored value with its label, ignoring only differences no filter would notice: case and spacing
    of text, the order of a list, and rounding below half a cent.

    A passage copied as written, such as a notice period, a service level, a product name or a place of jurisdiction,
    has no one right extent: "trois mois" and "trois mois avant son échéance" state the same period. It matches when it
    holds its label, or is a part of it that keeps at least two words and every number. A list of passages that misses
    some but invents none is incomplete, not wrong.
    """

    _NUMBER: ClassVar[re.Pattern[str]] = re.compile(r"\d+")
    PASSAGE_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            DocumentAttribute.NOTICE_PERIOD.value,
            DocumentAttribute.SERVICE_LEVELS.value,
            DocumentAttribute.PRODUCT.value,
            DocumentAttribute.JURISDICTION.value,
        }
    )

    @classmethod
    def outcome(cls, key: str, expected: Any, stored: Any, raw: Any) -> AttributeOutcome:
        if cls._is_empty(expected):
            return AttributeOutcome.CORRECT if cls._is_empty(stored) else AttributeOutcome.GUESSED
        if cls._is_empty(stored):
            return AttributeOutcome.EMPTY if cls._is_empty(raw) else AttributeOutcome.NOT_UNDERSTOOD
        if key in cls.PASSAGE_KEYS:
            return cls._passages_outcome(expected, stored)
        return AttributeOutcome.CORRECT if cls._equal(expected, stored) else AttributeOutcome.WRONG

    @classmethod
    def _passages_outcome(cls, expected: Any, stored: Any) -> AttributeOutcome:
        expected_items = expected if isinstance(expected, list) else [expected]
        stored_items = stored if isinstance(stored, list) else [stored]
        if not all(any(cls._overlap(item, wanted) for wanted in expected_items) for item in stored_items):
            return AttributeOutcome.WRONG
        if all(any(cls._overlap(item, wanted) for item in stored_items) for wanted in expected_items):
            return AttributeOutcome.CORRECT
        return AttributeOutcome.INCOMPLETE

    @classmethod
    def _overlap(cls, stored: Any, expected: Any) -> bool:
        """Whether a stored passage states its label: it holds the label, or it is a part of the label with at least
        two words and every number the label has, so "3" or "Monate" does not pass for "3 Monate"."""
        stored_text, expected_text = cls._passage(stored), cls._passage(expected)
        if expected_text in stored_text:
            return True
        return (
            stored_text in expected_text
            and len(stored_text.split()) >= 2
            and set(cls._NUMBER.findall(expected_text)) <= set(cls._NUMBER.findall(stored_text))
        )

    @classmethod
    def _equal(cls, expected: Any, stored: Any) -> bool:
        if isinstance(expected, list) and isinstance(stored, list):
            return {cls._text(item) for item in expected} == {cls._text(item) for item in stored}
        if isinstance(expected, int | float) and isinstance(stored, int | float):
            return abs(float(expected) - float(stored)) < _AMOUNT_TOLERANCE
        return cls._text(expected) == cls._text(stored)

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == [] or value == ""

    @staticmethod
    def _text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value)).strip().casefold()

    @classmethod
    def _passage(cls, value: Any) -> str:
        return re.sub(r"[\W_]+", " ", cls._text(value)).strip()
