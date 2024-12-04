from dagster import (
    AssetIn,
    AssetKey,
    AutomationCondition,
    DynamicPartitionsDefinition,
    Output,
    graph_asset,
)

from pipelines_core.ops.data_lake.data_lake_file_to_ref_doc import (
    data_lake_file_to_ref_doc,
)
from pipelines_core.ops.document.insert_ref_doc_into_docstore import (
    insert_ref_doc_into_docstore,
)
from pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.types.RefDocDocument import RefDocDocument
from pipelines_core.util.key_utils import group_name_from_asset_key


def documents_factory(
    key: AssetKey, data_lake_key: str, partitions: DynamicPartitionsDefinition
) -> graph_asset:
    """Creates a document asset that represents a Ref Doc in the Document Store.
    This asset takes a Data Lake File as input, parses it into a Ref Doc, and saves the corresponding
    Ref Doc with the text content into the Document store, as well as providing it as an output for
    downstream assets.
    """

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        ins={"data_lake_file": AssetIn(key=data_lake_key)},
        partitions_def=partitions,
        automation_condition=AutomationCondition.eager(),
        description="Create RefDocs from data lake files and insert them into the docstore",
    )
    def document(data_lake_file: DataLakeFile) -> Output[RefDocDocument]:
        return insert_ref_doc_into_docstore(data_lake_file_to_ref_doc(data_lake_file))

    return document
