from dagster import AssetIn, AssetKey, Output, graph_asset

from swiss_ai_hub.pipeline.ops.document.add_metadata_to_ref_docs import add_metadata_to_ref_docs
from swiss_ai_hub.pipeline.ops.document.delete_removed_ref_docs_from_docstore import (
    delete_removed_ref_docs_from_docstore,
)
from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile
from swiss_ai_hub.pipeline.types.RefDocDocument import RefDocDocument
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def removed_documents_factory(key: AssetKey, data_lake_key: str | AssetKey) -> graph_asset:
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
        description="Removes documents from the Doc Store that are no longer present in the Data Lake",
    )
    def removed_documents(
        data_lake_files: list[DataLakeFile],
    ) -> Output[list[RefDocDocument]]:
        return add_metadata_to_ref_docs(delete_removed_ref_docs_from_docstore(data_lake_files))

    return removed_documents
