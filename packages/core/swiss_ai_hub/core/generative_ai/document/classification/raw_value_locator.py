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
        return bool(cls.found_in([raw], document_text))

    @classmethod
    def found_in(cls, raws: list[str], document_text: str) -> list[str]:
        """The copies that are in the document, normalising the document once for all of them."""
        text = cls._comparable(document_text)
        squeezed = text.replace(" ", "")
        found = []
        for raw in raws:
            wanted = cls._comparable(raw)
            if wanted and (wanted in text or wanted.replace(" ", "") in squeezed):
                found.append(raw)
        return found

    @classmethod
    def line_of(cls, raw: str, document_text: str) -> str | None:
        """The document's lines that hold the copied text, for the words around it the model left out."""
        return next(iter(cls.passages_holding(raw, document_text, 1)), None)

    @classmethod
    def passages_holding(cls, raw: str, document_text: str, line_count: int) -> list[str]:
        """Each run of lines that holds the copied text, with the `line_count - 1` non-empty lines before it (a
        heading).

        The copy is found across line breaks and, failing that, with spacing ignored, just as `appears_in` finds it, but
        only as whole words: a short copy such as a city must not count where it stands inside another word.
        """
        wanted = cls._comparable(raw)
        if not wanted:
            return []
        lines = [line for line in document_text.splitlines() if line.strip()]
        comparable_lines = [cls._comparable(line) for line in lines]
        text = " ".join(comparable_lines)
        line_ends = list(itertools.accumulate(len(line) + 1 for line in comparable_lines))
        positions = cls._positions(wanted, text) or cls._positions(wanted, text, squeezed=True)
        spans = {
            (bisect.bisect_right(line_ends, start), bisect.bisect_right(line_ends, end)): None
            for start, end in positions
        }
        return ["\n".join(lines[max(0, first - line_count + 1) : last + 1]) for first, last in spans]

    @classmethod
    def _positions(cls, wanted: str, text: str, squeezed: bool = False) -> list[tuple[int, int]]:
        """Where `wanted` stands in `text` as whole words: its first and last character.

        Squeezed, spacing is ignored on both sides for OCR text, and the word boundaries are still read in `text`, so
        "Bern" is not found inside "Übernehmerin".
        """
        kept = [index for index, character in enumerate(text) if character != " "] if squeezed else None
        searched = "".join(text[index] for index in kept) if kept is not None else text
        needle = wanted.replace(" ", "") if squeezed else wanted
        positions = []
        position = searched.find(needle)
        while position >= 0:
            start, end = position, position + len(needle) - 1
            if kept is not None:
                start, end = kept[start], kept[end]
            if cls._whole_words(text, start, end):
                positions.append((start, end))
            position = searched.find(needle, position + 1)
        return positions

    @staticmethod
    def _whole_words(text: str, start: int, end: int) -> bool:
        opens = start == 0 or not (text[start - 1].isalnum() and text[start].isalnum())
        closes = end == len(text) - 1 or not (text[end].isalnum() and text[end + 1].isalnum())
        return opens and closes

    @classmethod
    def _comparable(cls, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        normalized = re.sub(r"[’‘`´]", "'", normalized)
        normalized = re.sub(r"[‐-―−]", "-", normalized)
        normalized = re.sub(r"[\\*_­]", "", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
