from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from mongoengine import connect


def connect_to_mongo_db(collection_name: str = None):
    cosmos_conn_singleton = CosmosAccess()
    host = cosmos_conn_singleton.get_connection_string()
    connect(
        db=ApiConfig().DB_NAME,
        host=host,
        alias="default",
    )
    if collection_name:
        connect(
            db=collection_name,
            host=host,
            alias=collection_name,
        )
