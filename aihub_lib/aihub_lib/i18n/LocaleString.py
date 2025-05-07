from typing import Optional

from pydantic import BaseModel, Field


class LocaleString(BaseModel):
    de: Optional[str] = Field(None)
    en: Optional[str] = Field(None)
    fr: Optional[str] = Field(None)
    it: Optional[str] = Field(None)

    def in_locale(self, locale: str) -> Optional[str]:
        return getattr(self, locale)

    @classmethod
    def from_i18n_path(cls, path: str):
        from aihub_lib.i18n.LocaleHandler import LocaleHandler

        return cls(
            de=LocaleHandler("de")(path),
            en=LocaleHandler("en")(path),
            fr=LocaleHandler("fr")(path),
            it=LocaleHandler("it")(path),
        )
