from mongoengine import connect
from swiss_ai_hub.core.infrastructure import MongoSettings


def connect_to_mongo_db(database_name: str | None = None):
    try:
        connect(
            db=database_name,
            host=MongoSettings().CONNECTION_STRING.get_secret_value(),
            uuidRepresentation="standard",
        )
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")
