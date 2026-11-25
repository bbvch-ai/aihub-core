from enum import StrEnum


class SearxngSafeSearch(StrEnum):
    """How strictly SearXNG asks its engines to filter adult content."""

    OFF = "off"
    MODERATE = "moderate"
    STRICT = "strict"

    @property
    def level(self) -> int:
        """The `safesearch` value SearXNG's API takes."""
        return list(SearxngSafeSearch).index(self)
