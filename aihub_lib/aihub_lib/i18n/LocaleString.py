from typing import Annotated

from pydantic import BaseModel, Field


class LocaleString(BaseModel):
    de: Annotated[str | None, Field(description="German")] = None
    en: Annotated[str | None, Field(description="English")] = None
    fr: Annotated[str | None, Field(description="French")] = None
    it: Annotated[str | None, Field(description="Italian")] = None

    def in_locale(self, locale: str) -> str | None:
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
