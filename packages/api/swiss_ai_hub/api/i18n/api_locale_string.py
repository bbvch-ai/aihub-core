from typing import Self

from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler


class ApiLocaleString(LocaleString):
    """LocaleString subclass that uses ApiLocaleHandler for translation resolution.

    Use this class for i18n paths that reference api translations (api.*.*)
    instead of the base LocaleString.from_i18n_path().
    """

    @classmethod
    def from_i18n_path(cls, path: str) -> Self:
        """Create an ApiLocaleString from an i18n translation path."""
        return cls(
            de=ApiLocaleHandler("de")(path),
            en=ApiLocaleHandler("en")(path),
            fr=ApiLocaleHandler("fr")(path),
            it=ApiLocaleHandler("it")(path),
        )
