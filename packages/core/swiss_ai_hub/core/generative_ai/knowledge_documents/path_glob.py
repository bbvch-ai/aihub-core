import unicodedata
from pathlib import PurePosixPath

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError

_MAX_ALTERNATIVES = 64


class PathGlob:
    """A glob over document paths in the dialect models already write: shell and ripgrep globs.

    `*` stays within one folder, `**` spans any number of folders including none, and `{pdf,docx}` lists
    alternatives. Matching ignores case, because synced file names mix `.PDF` and `.pdf`, and compares NFC-normalised
    text, because macOS and SMB sources store umlauts decomposed while a typed pattern is composed. The whole path must
    match, so `invoices/**` never matches `archive/invoices/x`.
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        normalized = unicodedata.normalize("NFC", pattern).lstrip("/")
        if not normalized:
            raise InvalidPathPatternError(pattern, "the pattern is empty; use '**' to match every document")
        self._alternatives = self._expand_braces(normalized)
        if len(self._alternatives) > _MAX_ALTERNATIVES:
            raise InvalidPathPatternError(
                pattern, f"its braces expand to more than {_MAX_ALTERNATIVES} patterns; use fewer alternatives"
            )

    def matches(self, path: str) -> bool:
        candidate = PurePosixPath(unicodedata.normalize("NFC", path))
        return any(candidate.full_match(alternative, case_sensitive=False) for alternative in self._alternatives)

    @staticmethod
    def _expand_braces(pattern: str) -> list[str]:
        group = PathGlob._first_brace_group(pattern)
        if group is None:
            return [pattern]
        start, end, alternatives = group
        prefix, suffix = pattern[:start], pattern[end + 1 :]
        expansions: list[str] = []
        for alternative in alternatives:
            expansions.extend(PathGlob._expand_braces(f"{prefix}{alternative}{suffix}"))
        return expansions

    @staticmethod
    def _first_brace_group(pattern: str) -> tuple[int, int, list[str]] | None:
        """The first `{...}` holding a top-level comma; a brace pair without one is literal, as in the shell."""
        for start, char in enumerate(pattern):
            if char == "{" and (group := PathGlob._brace_group_at(pattern, start)) is not None:
                return group
        return None

    @staticmethod
    def _brace_group_at(pattern: str, start: int) -> tuple[int, int, list[str]] | None:
        depth = 0
        alternatives: list[str] = []
        alternative_start = start + 1
        for index in range(start, len(pattern)):
            char = pattern[index]
            if char == "{":
                depth += 1
            elif char == "," and depth == 1:
                alternatives.append(pattern[alternative_start:index])
                alternative_start = index + 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    alternatives.append(pattern[alternative_start:index])
                    return (start, index, alternatives) if len(alternatives) > 1 else None
        return None
