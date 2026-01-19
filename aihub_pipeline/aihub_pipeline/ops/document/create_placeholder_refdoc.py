from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    HASH,
    INSERTED_AT,
    IS_INGESTED,
    NAMESPACE,
    NODE_CONTENT_TYPE,
    NODE_CONTENT_TYPE_TEXT,
    NODE_TYPE_CONTENT,
    SOURCE,
    TYPE,
    UPDATED_AT,
)
from dagster import Out, Output, op

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(out=Out(io_manager_key="doc_store_io_manager"))
def create_placeholder_refdoc_from_data_lake_file(
    data_lake_file: DataLakeFile,
) -> Output[RefDocDocument]:
    """Create a placeholder RefDocDocument (not yet ingested) from a DataLakeFile."""
    doc = RefDocDocument(text="")
    doc.id_ = data_lake_file.id_

    uri_parts = data_lake_file.uri.split("/")
    document_title = uri_parts[-1]

    doc.metadata = {
        **data_lake_file.metadata,
        NAMESPACE: data_lake_file.metadata.get(NAMESPACE, data_lake_file.namespace),
        HASH: data_lake_file.metadata.get(HASH, data_lake_file.hash),
        UPDATED_AT: int(data_lake_file.metadata.get(UPDATED_AT, data_lake_file.updated)),
        CREATED_AT: int(data_lake_file.metadata.get(CREATED_AT, data_lake_file.updated)),
        INSERTED_AT: int(data_lake_file.updated),
        TYPE: NODE_TYPE_CONTENT,
        NODE_CONTENT_TYPE: NODE_CONTENT_TYPE_TEXT,
        SOURCE: data_lake_file.uri,
        DOCUMENT_TITLE: data_lake_file.metadata.get(DOCUMENT_TITLE, document_title),
        IS_INGESTED: False,
    }

    return Output(doc)
