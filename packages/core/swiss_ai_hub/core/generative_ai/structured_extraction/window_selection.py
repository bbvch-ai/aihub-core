from typing import Annotated

import regex

# The terms come from a model, so a pathological pattern must not stall the extraction: each window gets this long.
TERM_SEARCH_SECONDS = 1.0


class WindowSelection:
    """Which windows of a long document to read when not all of them are.

    The opening window always, since it states what every record shares (an invoice number, the contract parties);
    then the windows where the lines holding wanted records most likely are, by how often the caller's row terms occur;
    any remaining room spread evenly over the document, so a document whose lines name none of the terms is still
    sampled from beginning to end. A partial read can miss records, which is why its result says it is partial.
    """

    @staticmethod
    def choose(
        windows: Annotated[list[str], "The document's windows, in order"],
        limit: Annotated[int, "The most windows to read"],
        row_terms: Annotated[str | None, "Words or a regular expression wanted lines usually contain"] = None,
    ) -> list[int]:
        """Positions of the windows to read, in document order."""
        if len(windows) <= limit:
            return list(range(len(windows)))
        hits = WindowSelection._hits(windows, row_terms)
        ranked = sorted((position for position in range(1, len(windows)) if hits[position]), key=lambda p: -hits[p])
        chosen = {0, *ranked[: limit - 1]}
        spread = (round(step * (len(windows) - 1) / max(1, limit - 1)) for step in range(limit))
        for position in spread:
            if len(chosen) >= limit:
                break
            chosen.add(position)
        for position in range(len(windows)):
            if len(chosen) >= limit:
                break
            chosen.add(position)
        return sorted(chosen)

    @staticmethod
    def _hits(windows: list[str], row_terms: str | None) -> list[int]:
        pattern = WindowSelection._pattern(row_terms)
        if pattern is None:
            return [0] * len(windows)
        return [WindowSelection._count(pattern, window) for window in windows]

    @staticmethod
    def _count(pattern: regex.Pattern[str], window: str) -> int:
        try:
            return len(pattern.findall(window, timeout=TERM_SEARCH_SECONDS, concurrent=True))
        except TimeoutError:
            return 0

    @staticmethod
    def _pattern(row_terms: str | None) -> regex.Pattern[str] | None:
        """The terms as a case-insensitive pattern; terms that are not a valid pattern count as plain words."""
        if not row_terms or not row_terms.strip():
            return None
        try:
            return regex.compile(row_terms, regex.IGNORECASE | regex.V1)
        except regex.error:
            words = [regex.escape(word.strip()) for word in row_terms.split("|") if word.strip()]
            return regex.compile("|".join(words), regex.IGNORECASE) if words else None
