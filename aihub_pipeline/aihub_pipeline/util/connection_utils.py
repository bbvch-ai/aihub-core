from mongoengine import connect

from aihub_lib.infrastructure.azure import BaseConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess


def connect_to_mongo_db(shortname: str = None):
    cosmos_conn_singleton = CosmosAccess()
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
