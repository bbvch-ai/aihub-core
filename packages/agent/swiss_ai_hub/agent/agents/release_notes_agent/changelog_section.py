from enum import StrEnum
from typing import Self

# Jira lets every site rename its issue types and ships them translated, so the common names of each language map to
# a section. A type not listed (Task, Sub-task, Epic, Service Request, a custom type) goes to Other.
_SECTION_OF_TYPE = {
    "bug": "fixes",
    "defect": "fixes",
    "fehler": "fixes",
    "bogue": "fixes",
    "anomalie": "fixes",
    "errore": "fixes",
    "story": "features",
    "user story": "features",
    "new feature": "features",
    "feature": "features",
    "neue funktion": "features",
    "nouvelle fonctionnalité": "features",
    "fonctionnalité": "features",
    "nuova funzionalità": "features",
    "funzionalità": "features",
    "improvement": "improvements",
    "enhancement": "improvements",
    "verbesserung": "improvements",
    "amélioration": "improvements",
    "miglioramento": "improvements",
}


class ChangelogSection(StrEnum):
    """Where a ticket goes in the changelog, decided from its Jira issue type; members are in changelog order."""

    FEATURES = "features"
    FIXES = "fixes"
    IMPROVEMENTS = "improvements"
    OTHER = "other"

    @classmethod
    def of_issue_type(cls, issue_type: str | None) -> Self:
        return cls(_SECTION_OF_TYPE.get((issue_type or "").strip().casefold(), cls.OTHER))

    @property
    def rank(self) -> int:
        return list(ChangelogSection).index(self)
