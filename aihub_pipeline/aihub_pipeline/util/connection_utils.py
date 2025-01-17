from aihub_lib.infrastructure.azure import BaseConfig, CosmosConnectionStringSingleton
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
