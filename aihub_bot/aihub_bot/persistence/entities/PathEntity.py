from typing import Optional

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField


class Credentials(EmbeddedDocument):
    APP_TYPE = StringField(required=False)
    APP_ID = StringField(required=False)
    APP_PASSWORD = StringField(required=False)
    APP_TENANTID = StringField(required=False)


class PathEntity(Document):
    meta = {
        "collection": "paths",
        "strict": False,
    }
    path = StringField(required=True)
    credentials = EmbeddedDocumentField(Credentials, required=True)

    @classmethod
    def get_credentials_by_path(cls, path: str) -> Optional[Credentials]:
        doc = cls.objects().filter(path=path).first()
        return doc.credentials if doc else None
