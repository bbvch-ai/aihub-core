from typing import List

from dagster import graph_asset, AutomationCondition, Output, AssetIn, AssetKey

from pipelines_core.ops.document.add_metadata_to_ref_docs import add_metadata_to_ref_docs
from pipelines_core.ops.document.delete_removed_ref_docs_from_docstore import delete_removed_ref_docs_from_docstore
from pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.types.RefDocDocument import RefDocDocument
from pipelines_core.util.key_utils import group_name_from_asset_key


def removed_documents_factory(key: AssetKey, data_lake_key: str) -> graph_asset:
    """Pseudo-Asset that removes documents from the document store and vector store that are no longer present
    in the Data Lake.
    This asset takes a list of DataLakeFiles as input, compares the documents in the Data Lake to the documents
    in the Doc Store, and removes any documents that are no longer present in the Data Lake from the Doc Store
    as well as the corresponding nodes in the Vector Store.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"data_lake_files": AssetIn(key=data_lake_key)},
        automation_condition=AutomationCondition.eager(),
        description="Removes documents from the Doc Store that are no longer present in the Data Lake",
    )
    def removed_documents(data_lake_files: List[DataLakeFile]) -> Output[List[RefDocDocument]]:
        return add_metadata_to_ref_docs(delete_removed_ref_docs_from_docstore(data_lake_files))

    return removed_documents
