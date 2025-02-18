from typing import Optional

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField


class Credentials(EmbeddedDocument):
    APP_TYPE = StringField(required=False)
    APP_ID = StringField(required=False)
    APP_PASSWORD = StringField(required=False)
    APP_TENANTID = StringField(required=False)


class PathEntity(Document):
    """
    Represents the configuration for a given path/endpoint and therefore for a specific bot.

    ### Purpose
    - Stores the credentials required to authenticate with a given bot.
    - Stores the system message with instructions for the bot.

    ### Key Fields
    - `path`: The path/endpoint for which the configuration is stored.
    - `credentials`: The credentials required to authenticate with the bot.
    - `system_message`: The system message with instructions for the bot.

    ### Methods
    - `get_credentials_by_path`: Retrieve the credentials for a given path.
    - `get_system_message_by_path`: Retrieve the system message for a given path.

    ### Usage
    This class enables the AI Hub to configure deployed bots with the necessary credentials and system messages
    directly in the database.
    """

    meta = {
        "collection": "paths",
        "strict": True,
    }
    path = StringField(required=True)
    credentials = EmbeddedDocumentField(Credentials, required=True)
    system_message = StringField(required=False)

    @classmethod
    def get_credentials_by_path(cls, path: str) -> Optional[Credentials]:
        doc = cls.objects().filter(path=path).first()
        return doc.credentials if doc else None

    @classmethod
    def get_system_message_by_path(cls, path: str) -> Optional[str]:
        doc = cls.objects().filter(path=path).first()
        return doc.system_message if doc else None
