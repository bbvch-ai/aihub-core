from enum import StrEnum
from typing import Self


class DocumentMetadataVerdict(StrEnum):
    """How a document's ingested type and attributes stand against a request's metadata filter.

    `UNKNOWN` keeps the document: an unclassified document or an empty value says nothing about it, so the extraction's
    document condition judges it instead.
    """

    MATCH = "match"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"

    @classmethod
    def combined(cls, verdicts: list[Self]) -> Self:
        """Every part must match: one exclusion excludes, otherwise one unknown part leaves the document unknown."""
        if cls.EXCLUDED in verdicts:
            return cls.EXCLUDED
        if cls.UNKNOWN in verdicts:
            return cls.UNKNOWN
        return cls.MATCH
