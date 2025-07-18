from mongoengine import EmbeddedDocument, StringField


class LocaleStringEntity(EmbeddedDocument):
    """
    An embedded document for storing internationalized strings in MongoDB.
    """

    meta = {"allow_inheritance": True}

    de = StringField(null=True)
    en = StringField(null=True)
    fr = StringField(null=True)
    it = StringField(null=True)
