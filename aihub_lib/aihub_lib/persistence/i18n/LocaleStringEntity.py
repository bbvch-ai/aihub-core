from typing import Self

from mongoengine import EmbeddedDocument, StringField

from aihub_lib.i18n.LocaleString import LocaleString


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
    def from_locale_string(cls, locale_string: LocaleString) -> Self:
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
