import re
from typing import Any

from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome

_AMOUNT_TOLERANCE = 0.005


class AttributeComparison:
    """Compares one stored value with its label, ignoring only differences no filter would notice: case and spacing
    of text, the order of a list, and rounding below half a cent."""

    @classmethod
    def outcome(cls, expected: Any, stored: Any, raw: Any) -> AttributeOutcome:
        if cls._is_empty(expected):
            return AttributeOutcome.CORRECT if cls._is_empty(stored) else AttributeOutcome.GUESSED
        if cls._is_empty(stored):
            return AttributeOutcome.EMPTY if cls._is_empty(raw) else AttributeOutcome.NOT_UNDERSTOOD
        return AttributeOutcome.CORRECT if cls._equal(expected, stored) else AttributeOutcome.WRONG

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
