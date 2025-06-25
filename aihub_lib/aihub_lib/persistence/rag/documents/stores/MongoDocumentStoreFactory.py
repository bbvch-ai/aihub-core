from functools import cache

from llama_index.storage.docstore.mongodb import MongoDocumentStore

from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreAccess import CosmosDocstoreAccess


@cache
def create_mongo_document_store(document_store_name: str) -> MongoDocumentStore:
    cosmos_conn_singleton = CosmosDocstoreAccess()
    docstore = MongoDocumentStore.from_uri(
        uri=cosmos_conn_singleton.get_connection_string(),
        db_name=document_store_name,
        namespace="documents",
        node_collection_suffix="-data",
        ref_doc_collection_suffix="-ref-doc-info",
        metadata_collection_suffix="-metadata",
    )
    return docstore
