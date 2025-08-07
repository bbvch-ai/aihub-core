from pydantic import BaseModel


class LocaleStrings(BaseModel):
    en: str | None = None
    de: str | None = None
    fr: str | None = None
    it: str | None = None


class UpdateNamespaceRequest(BaseModel):
    display_name: LocaleStrings | None = None
    description: LocaleStrings | None = None