import mongoengine
from mongoengine import register_connection
from swiss_ai_hub.core.infrastructure import MongoSettings


def ensure_connection(db_name: str, db_alias: str) -> None:
    """Ensure a MongoDB connection is registered under ``db_alias``. Safe to call multiple times."""
    try:
        mongoengine.connection.get_connection(alias=db_alias)
    except Exception:
        register_connection(
            alias=db_alias,
            name=db_name,
            host=MongoSettings().CONNECTION_STRING.get_secret_value(),
            uuidRepresentation="standard",
        )
