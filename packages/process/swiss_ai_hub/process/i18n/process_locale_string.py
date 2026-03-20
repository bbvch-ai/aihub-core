from typing import Self

from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.process.i18n.process_locale_handler import ProcessLocaleHandler


class ProcessLocaleString(LocaleString):
    """LocaleString subclass that uses ProcessLocaleHandler for translation resolution.

    Use this class for i18n paths that reference process translations (process.*.*)
    instead of the base LocaleString.from_i18n_path().
    """

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        """Create a ProcessLocaleString from an i18n translation path."""
        return cls(
            de=ProcessLocaleHandler("de")(path),
            en=ProcessLocaleHandler("en")(path),
            fr=ProcessLocaleHandler("fr")(path),
            it=ProcessLocaleHandler("it")(path),
        )
