import re
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK


class DocumentOpeningText:
    """The part of a document the classifier reads: its first pages, capped in characters, the clauses of its middle
    that state a term, a notice period, a court or the signing date, and its end.

    What a document is, who issued it and when sits on its first pages; totals, signatures and payment terms often sit
    on its last. A long contract states its term and its court in numbered articles between the two, and is signed
    before its annexes, so those few clauses are read from the middle too. The caps keep one dense page, or a contract
    that names its notice in every article, from filling the prompt, and every character also costs PII-detection time
    before an external model. Text without page breaks (older parses, non-MinerU loaders) is cut by the cap alone.
    Nothing is read twice.
    """

    PAGES: ClassVar[int] = 2
    MAX_OPENING_CHARACTERS: ClassVar[int] = 8000
    TAIL_CHARACTERS: ClassVar[int] = 1500
    CLAUSES_PER_KIND: ClassVar[int] = 2
    CLAUSE_CHARACTERS: ClassVar[int] = 500
    CLAUSE_LINES: ClassVar[int] = 5
    HEADING_CHARACTERS: ClassVar[int] = 60
    GAP: ClassVar[str] = "\n\n[…]\n\n"
    CLAUSE_KINDS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(
            r"laufzeit|vertragsdauer|vertragsbeginn|inkrafttreten|in kraft|dauer des vertrag|durée|entre en vigueur|"
            r"prend effet|durata|decorre|in vigore|\bterm\b|commence|effective date",
            re.IGNORECASE,
        ),
        re.compile(r"kündig|résili|préavis|disdett|recesso|terminat|non-renewal|notice period", re.IGNORECASE),
        re.compile(
            r"gerichtsstand|for juridique|tribuna|\bforo\b|jurisdiction|courts? of|governing law", re.IGNORECASE
        ),
        re.compile(
            r"ort und datum|ort, datum|fait à|luogo e data|place and date|signed (?:at|in|on)|"
            r"^\W*[A-ZÄÖÜ][\w .'-]{1,30},\s*(?:den|le|il|am)?\s*\d{1,2}\.?\s*\w+\.?\s*\d{4}\b",
            re.IGNORECASE,
        ),
    )
    """Term, notice, court and signing date, in German, French, Italian and English. Notice is read only where it ends
    the contract: an English contract gives "notice" of maintenance, price changes and audits too."""
    _YEAR: ClassVar[re.Pattern[str]] = re.compile(r"\b(?:19|20)\d{2}\b")

    @classmethod
    def of(cls, text: str) -> str:
        pages = [page.strip() for page in text.split(PAGE_BREAK)]
        first_pages = "\n\n".join(pages[: cls.PAGES]).strip()
        opening = cls._capped(first_pages)
        rest = "\n\n".join([first_pages[len(opening) :], *pages[cls.PAGES :]]).strip()
        if not rest:
            return opening
        tail = cls._tail(rest)
        clauses = cls._clauses(rest[: len(rest) - len(tail)] if tail else rest)
        return cls.GAP.join([opening, *clauses, tail])

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

    @classmethod
    def _clauses(cls, middle: str) -> list[str]:
        """The first lines of each kind in the middle, each with the lines after it, in the order written.

        A line that states a year, or a heading such as "§ 12 Gerichtsstand" whose next lines state the clause, comes
        before a line that only mentions the word in passing ("during the Subscription Term").
        """
        lines = [line.strip() for line in middle.splitlines() if line.strip()]
        chosen: set[int] = set()
        for kind in cls.CLAUSE_KINDS:
            matching = [index for index, line in enumerate(lines) if kind.search(line)]
            telling = [index for index in matching if cls._tells(lines[index])]
            chosen.update((telling + [index for index in matching if index not in telling])[: cls.CLAUSES_PER_KIND])
        clauses: list[str] = []
        covered = -1
        for index in sorted(chosen):
            if index <= covered:
                continue
            covered = min(index + cls.CLAUSE_LINES - 1, len(lines) - 1)
            clauses.append("\n".join(lines[index : covered + 1])[: cls.CLAUSE_CHARACTERS].strip())
        return clauses

    @classmethod
    def _tells(cls, line: str) -> bool:
        return len(line) <= cls.HEADING_CHARACTERS or bool(cls._YEAR.search(line))
