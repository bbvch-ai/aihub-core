from typing import Annotated

import mongoengine
from mongoengine import register_connection
from mongoengine.connection import ConnectionFailure

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings


class MongoConnectionRegistry:
    """Registers per-database mongoengine aliases on first use.

    Knowledge databases are created at runtime, so their aliases cannot be registered at startup like
    the main connection is.
    """

    @staticmethod
    def ensure_alias(
        db_name: Annotated[str, "Mongo database the alias points at"],
        alias: Annotated[str | None, "Alias to register; defaults to the database name"] = None,
    ) -> None:
        resolved_alias = alias or db_name
        try:
            mongoengine.connection.get_connection(alias=resolved_alias)
        except ConnectionFailure:
            # mongoengine's own ConnectionFailure, not pymongo's: the two are unrelated classes, and only
            # mongoengine's signals an unregistered alias. A reachability error must propagate.
            register_connection(
                alias=resolved_alias,
                name=db_name,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )
