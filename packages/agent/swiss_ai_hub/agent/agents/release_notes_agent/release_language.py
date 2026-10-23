from enum import StrEnum

_ENDONYMS = {"de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano"}
_ENGLISH_NAMES = {"de": "German", "en": "English", "fr": "French", "it": "Italian"}


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
