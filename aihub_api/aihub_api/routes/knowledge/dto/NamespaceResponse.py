from pydantic import BaseModel


class LocaleStrings(BaseModel):
    en: str | None = None
    de: str | None = None
    fr: str | None = None
    it: str | None = None


class NamespaceResponse(BaseModel):
    id: str
    bucket_id: str
    namespace_name: str
    folder_name: str
    display_name: LocaleStrings | None = None
    description: LocaleStrings | None = None