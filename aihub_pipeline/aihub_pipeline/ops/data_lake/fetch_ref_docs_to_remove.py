import mongoengine
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from dagster import OpExecutionContext, op
from mongoengine import register_connection

from aihub_pipeline.resources.doc_store.DocStoreResource import DocStoreResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument


def _ensure_connection(db_name: str, db_alias: str) -> None:
    """Ensure MongoDB connection is registered. Safe to call multiple times."""
    try:
        mongoengine.connection.get_connection(alias=db_alias)
    except Exception:
        register_connection(
            alias=db_alias,
            name=db_name,
            host=MongoSettings().CONNECTION_STRING.get_secret_value(),
            uuidRepresentation="standard",
        )


@op(code_version="v1")
def fetch_ref_docs_to_remove(
    context: OpExecutionContext, data_lake_files: list[DataLakeFile], doc_store_resource: DocStoreResource
) -> list[RefDocDocument]:
    """Fetches all RefDocs that are in the DocumentStore but no longer in the DataLake."""
    context.log.info(f"Reported {len(data_lake_files)} data lake files")
    ids = [data_lake_file.id_ for data_lake_file in data_lake_files]

    db_alias = doc_store_resource.document_store_name
    _ensure_connection(db_name=db_alias, db_alias=db_alias)

    ref_docs = RefDoc.get_documents(
        db_alias=db_alias,
        exclude_ids=ids,
    )

    context.log.info(f"Found {len(ref_docs)} ref docs that need to be removed")
    return [
        RefDocDocument(
            id_=str(ref_doc.id),
            text=ref_doc.data.text,
            metadata=ref_doc.data.metadata.to_mongo().to_dict(),
        )
        for ref_doc in ref_docs
    ]
