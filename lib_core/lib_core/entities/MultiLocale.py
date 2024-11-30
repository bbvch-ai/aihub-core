from mongoengine import (
    EmbeddedDocument,
    StringField,
)

class MultiLocale(EmbeddedDocument):
    de = StringField(required=False)
    en = StringField(required=False)
    it = StringField(required=False)
    fr = StringField(required=False)