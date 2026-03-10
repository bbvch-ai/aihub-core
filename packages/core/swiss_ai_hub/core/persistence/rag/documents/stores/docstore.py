from functools import cache

from llama_index.storage.docstore.mongodb import MongoDocumentStore

from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings


@cache
def create_mongo_document_store(document_store_name: str) -> MongoDocumentStore:
    return MongoDocumentStore.from_uri(
        uri=MongoSettings().CONNECTION_STRING.get_secret_value(),
        db_name=document_store_name,
        namespace="documents",
        node_collection_suffix="-data",
        ref_doc_collection_suffix="-ref-doc-info",
        metadata_collection_suffix="-metadata",
    )
