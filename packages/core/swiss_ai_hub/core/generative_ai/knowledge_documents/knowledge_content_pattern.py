import unicodedata

import regex

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_search_pattern_error import InvalidSearchPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_line import KnowledgeContentLine
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget

_MAX_QUERY_LENGTH = 500
# `regex`'s fuzzy constraints, e.g. `{e<=1}`: PCRE2 reads them as literal text, so the database would miss matches.
_FUZZY_CONSTRAINT = regex.compile(r"(?<!\\)\{[\d\s<=+,eisd]*[eisd][\d\s<=+,eisd]*\}")


class KnowledgeContentPattern:
    """A content search query, compiled once for the database's regex engine and once for Python's.

    The database (PCRE2) only finds candidate documents; Python's `regex` engine decides which lines match, so a
    document the two dialects disagree on is never reported with a line that does not match. The database pattern is
    prefixed with `(*UCP)`, without which PCRE2's `\\w` and `\\b` treat umlauts as non-word characters, and both sides
    use multiline mode, so `^` and `$` mean line boundaries as in grep. Text is stored as the parser wrote it, which on
    files from macOS or SMB sources can mean decomposed umlauts, so a composed query is also tried in its decomposed
    form; one alternation keeps that a single scan, where a second `$or` branch scanned every row twice. It is a branch
    reset group, `(?|…|…)`, because PCRE2 refuses a group name used twice, and the two copies of a named group must
    share their name and number. That covers literal text only: a character class such as `[üu]` matches one
    character, and a decomposed `ü` is two.

    PCRE2 stops at its backtracking limit, and DocumentDB reports that as no match, so a pattern with ambiguous nested
    repetition such as `(x+x+)+` or `(a|a)+` can miss documents without an error. Everyday patterns, `(\\w+\\s)+` and
    `.*` on 100k-character lines included, stay far below the limit.
    """

    def __init__(self, query: str, is_regex: bool = False, case_sensitive: bool = False) -> None:
        self.query = query
        self._reject_unusable(query, is_regex)
        normalized = unicodedata.normalize("NFC", query)
        composed = normalized if is_regex else regex.escape(normalized, special_only=True, literal_spaces=True)
        decomposed = unicodedata.normalize("NFD", composed)
        flags = regex.MULTILINE | (0 if case_sensitive else regex.IGNORECASE)
        self._composed = self._compile(composed, flags)
        self._decomposed = None if decomposed == composed else self._compile(decomposed, flags)
        if self._composed.search("") is not None:
            raise InvalidSearchPatternError(
                query, "it matches empty text, so every line would match; require at least one character"
            )
        alternatives = composed if self._decomposed is None else f"(?|(?:{composed})|(?:{decomposed}))"
        self.database_pattern = "(*UCP)" + alternatives
        self.database_options = "m" if case_sensitive else "mi"

    def matching_lines(
        self,
        text: str,
        limits: KnowledgeContentSearchLimits,
        budget: KnowledgeSearchBudget,
    ) -> tuple[list[KnowledgeContentLine], int]:
        """The first matching lines of a text and how many lines match in total.

        A line the decomposed variant alone matched also has to match the composed pattern once normalised: a class
        such as `[ü]` decomposes into a `u` and a combining diaeresis, and would then match a plain `u`. The check
        covers every line the match spans, so a match across a line break is not lost.
        """
        found = self._line_matches(self._composed, text, budget)
        if self._decomposed is not None:
            for line_start, (line_end, match) in self._line_matches(self._decomposed, text, budget).items():
                spanned = text[line_start : self._end_of_line(text, max(match.start(), match.end() - 1))]
                if line_start not in found and self._search(
                    self._composed, unicodedata.normalize("NFC", spanned), 0, budget
                ):
                    found[line_start] = (line_end, match)
        lines: list[KnowledgeContentLine] = []
        line_number, counted_to = 1, 0
        for line_start in sorted(found)[: limits.max_lines_per_document]:
            line_number += text.count("\n", counted_to, line_start)
            counted_to = line_start
            line_end, match = found[line_start]
            lines.append(
                KnowledgeContentLine.from_text(
                    text, line_start, line_end, line_number, match.start(), limits.max_line_chars
                )
            )
        return lines, len(found)

    def _line_matches(
        self, pattern: regex.Pattern[str], text: str, budget: KnowledgeSearchBudget
    ) -> dict[int, tuple[int, regex.Match[str]]]:
        """Start of every matching line, mapped to its end (without a trailing `\\r`) and its first match.

        One search per matching line, resumed after the line, so a word repeated thousands of times costs one
        search per line rather than one per occurrence. A match spanning lines counts for the line it starts on.
        """
        found: dict[int, tuple[int, regex.Match[str]]] = {}
        position = 0
        while position <= len(text) and (match := self._search(pattern, text, position, budget)) is not None:
            line_start = text.rfind("\n", 0, match.start()) + 1
            next_line = self._end_of_line(text, match.start())
            line_end = next_line - 1 if next_line > line_start and text[next_line - 1] == "\r" else next_line
            found[line_start] = (line_end, match)
            position = next_line + 1
        return found

    @staticmethod
    def _end_of_line(text: str, position: int) -> int:
        newline = text.find("\n", position)
        return len(text) if newline == -1 else newline

    @staticmethod
    def _search(
        pattern: regex.Pattern[str], text: str, position: int, budget: KnowledgeSearchBudget
    ) -> regex.Match[str] | None:
        try:
            return pattern.search(text, position, timeout=budget.remaining_seconds(), concurrent=True)
        except TimeoutError as timeout_error:
            raise budget.exhausted() from timeout_error

    @staticmethod
    def _reject_unusable(query: str, is_regex: bool) -> None:
        if not query:
            raise InvalidSearchPatternError(query, "it is empty; search for at least one character")
        if len(query) > _MAX_QUERY_LENGTH:
            raise InvalidSearchPatternError(
                query, f"it is longer than {_MAX_QUERY_LENGTH} characters; search for a shorter, distinctive part"
            )
        if "\0" in query:
            raise InvalidSearchPatternError(query, "it contains a NUL character, which no document text contains")
        if is_regex and _FUZZY_CONSTRAINT.search(query):
            raise InvalidSearchPatternError(
                query, "fuzzy constraints such as {e<=1} are not supported; spell out the alternatives instead"
            )

    def _compile(self, source: str, flags: int) -> regex.Pattern[str]:
        try:
            return regex.compile(source, flags)
        except regex.error as compile_error:
            raise InvalidSearchPatternError(
                self.query, f"{compile_error}; escape literal characters such as ( ) [ ] . + with a backslash"
            ) from compile_error
