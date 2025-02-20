from mongoengine import connect

from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess


def connect_to_mongo_db(database_name: str = None):
    cosmos_conn_singleton = CosmosAccess()
    host = cosmos_conn_singleton.get_connection_string()
    connect(
        db=database_name,
        host=host,
        alias="default",
    )
