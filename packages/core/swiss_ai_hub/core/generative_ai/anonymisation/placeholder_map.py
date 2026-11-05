import re
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.presidio_analyzer.analyzer_span import AnalyzerSpan


class PlaceholderMap(BaseModel):
    """The placeholders one conversation has issued (`<PERSON_1>` → "Anna Muster"), kept so they stay stable.

    A value gets one placeholder for the whole conversation, so the same person is `<PERSON_1>` in every message, and
    numbers are never reused. Detections that overlap are merged first, so a placeholder never covers half a value.
    Placeholders already in a text (an answer pasted back, or text anonymised elsewhere) are left alone and never
    issued again for a new value. The map holds personal data: keep it where the conversation itself is kept.
    """

    TOKEN: ClassVar[re.Pattern[str]] = re.compile(r"<[A-Z][A-Z_]*_\d+>")

    values: Annotated[dict[str, str], Field(description="Placeholder → original value.")] = {}
    next_number: Annotated[int, Field(description="The number the next new placeholder gets.")] = 1

    def placeholders_in(self, text: str) -> list[str]:
        return list(dict.fromkeys(self.TOKEN.findall(text)))

    def issued_in(self, text: str) -> bool:
        """Whether the text holds a placeholder this conversation issued, i.e. it should be restored."""
        return any(token in self.values for token in self.placeholders_in(text))

    def unknown_in(self, text: str) -> list[str]:
        """Placeholders in the text that this conversation never issued, which restoring leaves as they are."""
        return [token for token in self.placeholders_in(text) if token not in self.values]

    def restore(self, text: str) -> str:
        return self.TOKEN.sub(lambda match: self.values.get(match.group(0), match.group(0)), text)

    def mask(self, text: str, spans: list[AnalyzerSpan]) -> str:
        existing = [(match.start(), match.end()) for match in self.TOKEN.finditer(text)]
        spans = [span for span in spans if not any(span.start < end and start < span.end for start, end in existing)]
        reserved = set(self.placeholders_in(text))
        parts, cursor = [], 0
        for span in self.merge_overlaps(spans):
            parts += [
                text[cursor : span.start],
                self._placeholder_for(span.entity_type, text[span.start : span.end], reserved),
            ]
            cursor = span.end
        return "".join([*parts, text[cursor:]])

    @staticmethod
    def merge_overlaps(spans: list[AnalyzerSpan]) -> list[AnalyzerSpan]:
        """Overlapping detections become one, typed after the longest of them."""
        merged: list[AnalyzerSpan] = []
        for span in sorted(spans, key=lambda s: (s.start, -(s.end - s.start), s.entity_type)):
            previous = merged[-1] if merged else None
            if previous and span.start < previous.end:
                entity_type = (
                    span.entity_type if span.end - span.start > previous.end - previous.start else previous.entity_type
                )
                merged[-1] = previous.model_copy(
                    update={"end": max(previous.end, span.end), "entity_type": entity_type}
                )
            else:
                merged.append(span)
        return merged

    def _placeholder_for(self, entity_type: str, value: str, reserved: set[str]) -> str:
        entity_type = entity_type.upper()
        for token, known in self.values.items():
            if known == value and token[1:].rsplit("_", 1)[0] == entity_type:
                return token
        while True:
            token = f"<{entity_type}_{self.next_number}>"
            self.next_number += 1
            if token not in self.values and token not in reserved:
                self.values[token] = value
                return token
