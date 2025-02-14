from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField


class Credentials(EmbeddedDocument):
    app_id = StringField(required=True)
    app_password = StringField(required=True)


class PathEntity(Document):
    meta = {
        "collection": "paths",
        "strict": True,
    }
    path = StringField(required=True)
    credentials = EmbeddedDocumentField(Credentials, required=True)

    @classmethod
    def get_credentials_by_path(cls, path: str) -> Credentials:
        return cls.objects().filter(path=path).first().credentials
