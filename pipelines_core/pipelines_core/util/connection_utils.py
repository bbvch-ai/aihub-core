from lib_core.clients.CosmosConnectionStringSingleton import (
    CosmosConnectionStringSingleton,
)
from lib_core.config.BaseConfig import BaseConfig
from mongoengine import connect


def connect_to_mongo_db(shortname: str = None):
    cosmos_conn_singleton = CosmosConnectionStringSingleton()
    host = cosmos_conn_singleton.get_connection_string()
    connect(
        db=BaseConfig().SHARED_DB_NAME,
        host=host,
        alias="default",
    )
    if shortname:
        connect(
            db=shortname,
            host=host,
            alias=shortname,
        )
