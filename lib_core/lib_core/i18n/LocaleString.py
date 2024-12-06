from typing import Optional

from openai import BaseModel
from pydantic import Field


class LocaleString(BaseModel):
    de: Optional[str] = Field(None)
    en: Optional[str] = Field(None)
    fr: Optional[str] = Field(None)
    it: Optional[str] = Field(None)

    def in_locale(self, locale: str) -> Optional[str]:
        return getattr(self, locale)