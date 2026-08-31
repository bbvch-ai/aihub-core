from dagster import OpExecutionContext, op
from swiss_ai_hub.core.persistence import RefDoc

from swiss_ai_hub.pipeline.resources.doc_store.doc_store_resource import DocStoreResource
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.mongo_utils import ensure_connection


@op(code_version="v1")
def fetch_ref_docs_to_remove(
    context: OpExecutionContext, data_lake_files: list[DataLakeFile], doc_store_resource: DocStoreResource
) -> list[RefDocDocument]:
    """Fetches all RefDocs that are in the DocumentStore but no longer in the DataLake."""
    context.log.info(f"Reported {len(data_lake_files)} data lake files")
    ids = [data_lake_file.id_ for data_lake_file in data_lake_files]

    db_alias = doc_store_resource.document_store_name
    ensure_connection(db_name=db_alias, db_alias=db_alias)

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
