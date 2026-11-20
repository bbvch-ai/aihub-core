import bisect
import itertools
import re
import unicodedata


class RawValueLocator:
    """Checks that text the model copied really is in the document, so a value it invented is stored empty.

    Both sides are compared with case, Unicode forms, apostrophe and dash variants, markdown emphasis and spacing
    evened out, since parsed text and the model's copy differ in exactly those ways. Spacing is also ignored
    altogether, for OCR text that splits or joins words differently from the model.
    """

    @classmethod
    def appears_in(cls, raw: str, document_text: str) -> bool:
        wanted = cls._comparable(raw)
        if not wanted:
            return False
        text = cls._comparable(document_text)
        return wanted in text or wanted.replace(" ", "") in text.replace(" ", "")

    @classmethod
    def line_of(cls, raw: str, document_text: str) -> str | None:
        """The document's lines that hold the copied text, for the words around it the model left out."""
        return next(iter(cls.passages_holding(raw, document_text, 1)), None)

    @classmethod
    def passages_holding(cls, raw: str, document_text: str, line_count: int) -> list[str]:
        """Each run of lines that holds the copied text, with the `line_count - 1` non-empty lines before it (a
        heading).

        The copy is found across line breaks and, failing that, with spacing ignored, just as `appears_in` finds it.
        """
        wanted = cls._comparable(raw)
        if not wanted:
            return []
        lines = [line for line in document_text.splitlines() if line.strip()]
        comparable_lines = [cls._comparable(line) for line in lines]
        spans = cls._line_spans(wanted, comparable_lines, " ") or cls._line_spans(
            wanted.replace(" ", ""), [line.replace(" ", "") for line in comparable_lines], ""
        )
        return ["\n".join(lines[max(0, first - line_count + 1) : last + 1]) for first, last in spans]

    @classmethod
    def _line_spans(cls, wanted: str, lines: list[str], separator: str) -> list[tuple[int, int]]:
        """The first and last line of each place `wanted` stands, reading the lines as one text."""
        line_ends = list(itertools.accumulate(len(line) + len(separator) for line in lines))
        text = separator.join(lines)
        spans: dict[tuple[int, int], None] = {}
        position = text.find(wanted)
        while position >= 0:
            first = bisect.bisect_right(line_ends, position)
            last = bisect.bisect_right(line_ends, position + len(wanted) - 1)
            spans[(first, last)] = None
            position = text.find(wanted, position + 1)
        return list(spans)

    @classmethod
    def _comparable(cls, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        normalized = re.sub(r"[’‘`´]", "'", normalized)
        normalized = re.sub(r"[‐-―−]", "-", normalized)
        normalized = re.sub(r"[\\*_­]", "", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
