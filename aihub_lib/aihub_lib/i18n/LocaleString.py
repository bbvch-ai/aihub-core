from typing import Annotated

from mongoengine import EmbeddedDocument, StringField
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


class LocaleStringEntity(EmbeddedDocument):
    """
    A MongoEngine embedded document that represents a localized string.
    This is used to store localized strings in MongoDB.
    """

    de = StringField(required=False, null=True, description="German translation")
    en = StringField(required=False, null=True, description="English translation")
    fr = StringField(required=False, null=True, description="French translation")
    it = StringField(required=False, null=True, description="Italian translation")

    @classmethod
    def from_locale_string(cls, locale_string: LocaleString) -> "LocaleStringEntity":
        """Create a LocaleStringEntity from a LocaleString."""
        if locale_string is None:
            return cls()

        return cls(
            de=locale_string.de,
            en=locale_string.en,
            fr=locale_string.fr,
            it=locale_string.it,
        )

    def to_locale_string(self) -> LocaleString:
        """Convert this entity to a LocaleString."""
        return LocaleString(
            de=self.de,
            en=self.en,
            fr=self.fr,
            it=self.it,
        )
