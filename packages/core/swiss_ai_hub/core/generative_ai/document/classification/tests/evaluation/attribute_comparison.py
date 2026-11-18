import re
from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome

_AMOUNT_TOLERANCE = 0.005


class AttributeComparison:
    """Compares one stored value with its label, ignoring only differences no filter would notice: case and spacing
    of text, the order of a list, and rounding below half a cent.

    A passage copied as written, such as a notice period or a service level, has no one right extent: "trois mois" and
    "trois mois avant son échéance" state the same period. It matches when either contains the other. A list of
    passages that misses some but invents none is incomplete, not wrong.
    """

    PASSAGE_KEYS: ClassVar[frozenset[str]] = frozenset(
        {DocumentAttribute.NOTICE_PERIOD.value, DocumentAttribute.SERVICE_LEVELS.value}
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
    def _overlap(cls, first: Any, second: Any) -> bool:
        first_text, second_text = cls._passage(first), cls._passage(second)
        return first_text in second_text or second_text in first_text

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
