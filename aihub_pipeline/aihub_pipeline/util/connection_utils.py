from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreAccess import CosmosDocstoreAccess
from mongoengine import connect


def connect_to_mongo_db(database_name: str = None):
    try:
        cosmos_conn_singleton = CosmosDocstoreAccess()
        host = cosmos_conn_singleton.get_connection_string()
        connect(
            db=database_name,
            host=host,
        )
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")
