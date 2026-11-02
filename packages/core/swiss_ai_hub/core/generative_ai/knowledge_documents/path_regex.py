import time
import unicodedata

import regex

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError

_MAX_PATTERN_LENGTH = 500
_CALL_BUDGET_SECONDS = 0.5


class PathRegex:
    """A regular expression searched anywhere in a document path, like grep.

    Patterns usually come from a model, so they run on the `regex` engine under one time budget per call: the standard
    library's `re` backtracks without limit, and a budget per path would still let a pattern that stays just under it
    block the event loop for seconds across a few hundred paths. Paths and pattern are NFC-normalised for the same
    reason as in `PathGlob`.
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
        return self.matches_all([path])[0]

    def matches_all(self, paths: list[str]) -> list[bool]:
        """Whether each path matches, all within one shared time budget."""
        deadline = time.monotonic() + _CALL_BUDGET_SECONDS
        results: list[bool] = []
        for path in paths:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise self._too_slow()
            try:
                found = self._compiled.search(unicodedata.normalize("NFC", path), timeout=remaining)
            except TimeoutError as timeout_error:
                raise self._too_slow() from timeout_error
            results.append(found is not None)
        return results

    def _too_slow(self) -> InvalidPathPatternError:
        return InvalidPathPatternError(
            self.pattern, "it takes too long to match; avoid nested repetition such as (a+)+ or (a|a)*"
        )
