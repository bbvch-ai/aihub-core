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

    ### Usage
    This class enables the AI Hub to configure deployed bots with the necessary credentials and system messages
    directly in the database.
    """

    meta = {
        "collection": "bot_paths",
        "strict": True,
        "indexes": [
            {"fields": ["path"], "unique": True},
        ],
    }
    path = StringField(required=True)
    credentials = EmbeddedDocumentField(Credentials, required=True)
    system_message = StringField(required=False)
    slack_token = StringField(required=False)

    @classmethod
    def get_credentials_by_path(cls, path: str) -> Credentials | None:
        doc = cls.objects().filter(path=path).first()
        return doc.credentials if doc else None

    @classmethod
    def get_system_message_by_path(cls, path: str) -> str | None:
        doc = cls.objects().filter(path=path).first()
        return doc.system_message if doc else None

    @classmethod
    def get_slack_token_by_path(cls, path: str) -> str | None:
        doc = cls.objects().filter(path=path).first()
        return doc.slack_token if doc else None
