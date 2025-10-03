from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from dagster import OpExecutionContext, op
from mongoengine import disconnect

from aihub_pipeline.resources.doc_store.DocStoreResource import DocStoreResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.connection_utils import connect_to_mongo_db


@op(code_version="v1")
def fetch_ref_docs_to_remove(
    context: OpExecutionContext, data_lake_files: list[DataLakeFile], doc_store_resource: DocStoreResource
) -> list[RefDocDocument]:
    """Fetches all RefDocs that are in the DocumentStore but no longer in the DataLake."""
    context.log.info(f"Reported {len(data_lake_files)} data lake files")
    ids = [data_lake_file.id_ for data_lake_file in data_lake_files]

    connect_to_mongo_db(doc_store_resource.document_store_name)
    try:
        ref_docs = RefDoc.get_documents(
            db_alias="default",
            exclude_ids=ids,
        )
    finally:
        disconnect()

    context.log.info(f"Found {len(ref_docs)} ref docs that need to be removed")
    return [
        RefDocDocument(
            id_=str(ref_doc.id),
            text=ref_doc.data.text,
            metadata=ref_doc.data.metadata.to_mongo().to_dict(),
        )
        for ref_doc in ref_docs
    ]
