import unicodedata

import regex

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError

_MAX_PATTERN_LENGTH = 500
_SEARCH_TIMEOUT_SECONDS = 0.05


class PathRegex:
    """A regular expression searched anywhere in a document path, like grep.

    Patterns usually come from a model, so they run on the `regex` engine with a per-path timeout: the standard
    library's `re` backtracks without limit, and a pattern such as `^(\\w+\\w?)+$` keeps it busy for longer than any
    tool call should take. Paths and pattern are NFC-normalised for the same reason as in `PathGlob`.
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        if len(pattern) > _MAX_PATTERN_LENGTH:
            raise InvalidPathPatternError(
                pattern[:80] + "...",
                f"it is longer than {_MAX_PATTERN_LENGTH} characters; use a shorter pattern or a glob",
            )
        try:
            self._compiled = regex.compile(unicodedata.normalize("NFC", pattern))
        except regex.error as compile_error:
            raise InvalidPathPatternError(
                pattern, f"{compile_error}; escape literal characters such as ( ) [ ] . + with a backslash"
            ) from compile_error

    def matches(self, path: str) -> bool:
        try:
            return (
                self._compiled.search(unicodedata.normalize("NFC", path), timeout=_SEARCH_TIMEOUT_SECONDS) is not None
            )
        except TimeoutError as timeout_error:
            raise InvalidPathPatternError(
                self.pattern, "it takes too long to match; avoid nested repetition such as (a+)+ or (a|a)*"
            ) from timeout_error
