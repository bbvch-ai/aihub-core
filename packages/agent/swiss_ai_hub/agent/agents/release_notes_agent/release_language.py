import re
import unicodedata
from enum import StrEnum
from typing import Annotated, Self

_ENDONYMS = {"de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano"}
_ENGLISH_NAMES = {"de": "German", "en": "English", "fr": "French", "it": "Italian"}
# How a request asks for a language in each platform language: the word that asks, then the language's name as that
# language writes it ("in German", "auf Deutsch", "ins Deutsche", "en allemand", "in tedesco"). A name without the word
# is a country, a company or an adjective ("in Italien", "Deutsche Bahn", "English-speaking"), not a request.
_REQUESTS = (
    ("in|into", {"german": "de", "english": "en", "french": "fr", "italian": "it"}),
    ("auf|in", {"deutsch": "de", "englisch": "en", "französisch": "fr", "italienisch": "it"}),
    ("ins", {"deutsche": "de", "englische": "en", "französische": "fr", "italienische": "it"}),
    ("en", {"allemand": "de", "anglais": "en", "français": "fr", "francais": "fr", "italien": "it"}),
    ("in", {"tedesco": "de", "inglese": "en", "francese": "fr", "italiano": "it"}),
)
_PATTERNS = [
    (re.compile(rf"(?<!\w)(?:(?P<cue>{cues})\s+)?(?P<name>{'|'.join(names)})(?![\w-])"), names)
    for cues, names in _REQUESTS
]
_LIST_SEPARATOR = re.compile(r"\s*(?:,|&|/|(?<!\w)(?:and|und|et|e|or|oder|ou|o)(?!\w))\s*")


class ReleaseLanguage(StrEnum):
    """A language release notes are written or translated in; the platform's locales, so the changelog's headings
    exist in each."""

    DE = "de"
    EN = "en"
    FR = "fr"
    IT = "it"

    @property
    def endonym(self) -> str:
        """What the form shows: the option labels of a select are not localized, and a reader finds their own
        language by its own name."""
        return _ENDONYMS[self.value]

    @property
    def english_name(self) -> str:
        """What a prompt names, since the prompts are written in English."""
        return _ENGLISH_NAMES[self.value]

    @classmethod
    def named_in(
        cls, text: Annotated[str, "What the user asked, e.g. 'release notes for 2.0 in French'"]
    ) -> list[Self]:
        """The languages a message asks for, in the order it names them. A name counts after the word that asks for
        it ("in French", "auf Deutsch", "en français"), or listed right after one that counted, in the same language
        ("auf Deutsch und Englisch"); "für Kunden in Italien" and "for Deutsche Bahn" name none."""
        normalized = unicodedata.normalize("NFKC", text).casefold()
        requested: list[Self] = []
        previous: tuple[int, int] | None = None
        for start, end, group, language, cued in cls._names(normalized):
            listed = (
                previous is not None
                and previous[1] == group
                and _LIST_SEPARATOR.fullmatch(normalized[previous[0] : start]) is not None
            )
            if cued or listed:
                requested.append(cls(language))
                previous = (end, group)
        return list(dict.fromkeys(requested))

    @staticmethod
    def _names(text: str) -> list[tuple[int, int, int, str, bool]]:
        """Every language name written as a whole word, in text order: where it starts and ends, the group of
        `_REQUESTS` it belongs to, its language, and whether the word that asks for it comes right before it."""
        return sorted(
            (found.start("name"), found.end(), group, names[found["name"]], found["cue"] is not None)
            for group, (pattern, names) in enumerate(_PATTERNS)
            for found in pattern.finditer(text)
        )
