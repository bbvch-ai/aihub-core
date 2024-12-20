from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)


class ApiUser(EmbeddedDocument):
    name = StringField(required=True)
    email = StringField(required=True)


class AccessToken(Document):
    meta = {
        "collection": "accesstokens",
        "strict": False,
    }
    version = IntField(default=1, db_field="_version")
    expiry_date = DateTimeField(required=True)
    roles = ListField(StringField())
    user = EmbeddedDocumentField(ApiUser)

    @staticmethod
    def by_id(organization_shortname: str, token: str) -> "AccessToken":
        return AccessToken.objects.using(organization_shortname).get(id=token)
