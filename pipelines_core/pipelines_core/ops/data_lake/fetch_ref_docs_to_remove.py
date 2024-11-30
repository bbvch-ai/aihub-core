from typing import List

from dagster import op, OpExecutionContext

from lib_core.entities.RefDoc import RefDoc
from pipelines_core.pipelines_core.resources.organization.NamespaceResource import NamespaceResource
from pipelines_core.pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.pipelines_core.types.RefDocDocument import RefDocDocument
from pipelines_core.pipelines_core.util.connection_utils import connect_to_mongo_db


@op(code_version="v1")
def fetch_ref_docs_to_remove(
    context: OpExecutionContext,
    namespace: NamespaceResource,
    data_lake_files: List[DataLakeFile],
) -> List[RefDocDocument]:
    """Fetches all RefDocs that are int he DocumentStore but no longer in the DataLake"""
    context.log.info(f"Reported {len(data_lake_files)} data lake files")
    ids = [data_lake_file.id_ for data_lake_file in data_lake_files]

    connect_to_mongo_db(namespace.organization)
    ref_docs = RefDoc.by_namespace(
        organization_shortname=namespace.organization,
        namespace=namespace.name,
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
