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
        """The document's line that holds the copied text, for the words around it the model left out."""
        return next(iter(cls.passages_holding(raw, document_text, 1)), None)

    @classmethod
    def passages_holding(cls, raw: str, document_text: str, line_count: int) -> list[str]:
        """Each line that holds the copied text, with the `line_count - 1` non-empty lines before it (a heading)."""
        wanted = cls._comparable(raw)
        lines = [line for line in document_text.splitlines() if line.strip()]
        return [
            "\n".join(lines[max(0, index - line_count + 1) : index + 1])
            for index, line in enumerate(lines)
            if wanted and wanted in cls._comparable(line)
        ]

    @classmethod
    def _comparable(cls, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        normalized = re.sub(r"[’‘`´]", "'", normalized)
        normalized = re.sub(r"[‐-―−]", "-", normalized)
        normalized = re.sub(r"[\\*_­]", "", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
