from typing import Optional, Annotated

from pydantic import BaseModel, Field


class LocaleString(BaseModel):
    de: Annotated[Optional[str], Field(description="German")] = None
    en: Annotated[Optional[str], Field(description="English")] = None
    fr: Annotated[Optional[str], Field(description="French")] = None
    it: Annotated[Optional[str], Field(description="Italian")] = None

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
