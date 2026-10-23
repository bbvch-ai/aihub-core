import re
import unicodedata
from enum import StrEnum
from typing import Annotated, Self

_ENDONYMS = {"de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano"}
_ENGLISH_NAMES = {"de": "German", "en": "English", "fr": "French", "it": "Italian"}
# Each language by its name in every platform language, inflected the way a request names it ("auf Deutsch",
# "in German", "en allemand", "in tedesco").
_NAMES = {
    "de": ("german", "deutsch", "deutsche", "deutschen", "allemand", "allemande", "tedesco", "tedesca"),
    "en": ("english", "englisch", "englische", "englischen", "anglais", "anglaise", "inglese"),
    "fr": ("french", "französisch", "französische", "französischen", "français", "française", "francais", "francese"),
    "it": ("italian", "italienisch", "italienische", "italienischen", "italien", "italienne", "italiano", "italiana"),
}


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
        """The languages a message asks for, in the order it names them, as whole words only: "Germany" names none."""
        normalized = unicodedata.normalize("NFKC", text).casefold()
        found: dict[Self, int] = {}
        for language in cls:
            positions = [
                match.start()
                for name in _NAMES[language.value]
                for match in re.finditer(rf"(?<!\w){re.escape(name)}(?!\w)", normalized)
            ]
            if positions:
                found[language] = min(positions)
        return sorted(found, key=found.__getitem__)
