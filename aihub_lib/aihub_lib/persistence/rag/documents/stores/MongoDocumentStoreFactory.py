from functools import cache

from llama_index.storage.docstore.mongodb import MongoDocumentStore

from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess


@cache
def create_mongo_document_store(document_store_name: str) -> MongoDocumentStore:
    cosmos_conn_singleton = CosmosAccess()
    docstore = MongoDocumentStore.from_uri(
        uri=cosmos_conn_singleton.get_connection_string(),
        db_name=document_store_name,
        namespace="documents",  # Note: This is not "our" namespace, this is the collection name.
    )
    docstore._node_collection = docstore._node_collection.replace("/", "-")
    docstore._ref_doc_collection = docstore._ref_doc_collection.replace("/", "-")
    docstore._metadata_collection = docstore._metadata_collection.replace("/", "-")
    return docstore
