from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK


class DocumentOpeningText:
    """The part of a document the classifier reads: its first pages, capped in characters, plus its end.

    What a document is, who issued it and when sits on its first pages; totals, signatures and payment terms often sit
    on its last. The cap keeps one page that is a dense table from filling the prompt, and every character also costs
    PII-detection time before an external model. Text without page breaks (older parses, non-MinerU loaders) is cut by
    the cap alone. The end is taken from what the opening left out, so nothing is read twice.
    """

    PAGES: ClassVar[int] = 2
    MAX_OPENING_CHARACTERS: ClassVar[int] = 8000
    TAIL_CHARACTERS: ClassVar[int] = 1500
    GAP: ClassVar[str] = "\n\n[…]\n\n"

    @classmethod
    def of(cls, text: str) -> str:
        pages = [page.strip() for page in text.split(PAGE_BREAK)]
        first_pages = "\n\n".join(pages[: cls.PAGES]).strip()
        opening = cls._capped(first_pages)
        rest = "\n\n".join([first_pages[len(opening) :], *pages[cls.PAGES :]]).strip()
        if not rest:
            return opening
        return f"{opening}{cls.GAP}{cls._tail(rest)}"

    @classmethod
    def _capped(cls, text: str) -> str:
        """The text up to the cap, cut at the last paragraph end before it when that keeps at least half."""
        if len(text) <= cls.MAX_OPENING_CHARACTERS:
            return text
        cut = text[: cls.MAX_OPENING_CHARACTERS]
        paragraph_end = cut.rfind("\n\n")
        return (cut[:paragraph_end] if paragraph_end > cls.MAX_OPENING_CHARACTERS // 2 else cut).rstrip()

    @classmethod
    def _tail(cls, rest: str) -> str:
        """The last characters of what the opening left out, starting at a line where one starts within them."""
        if len(rest) <= cls.TAIL_CHARACTERS:
            return rest
        tail = rest[-cls.TAIL_CHARACTERS :]
        line_start = tail.find("\n")
        return (tail[line_start + 1 :] if 0 <= line_start < len(tail) - 1 else tail).strip()
