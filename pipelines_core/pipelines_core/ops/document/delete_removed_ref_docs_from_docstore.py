from typing import List

from dagster import Output, graph

from pipelines_core.ops.data_lake.fetch_ref_docs_to_remove import (
    fetch_ref_docs_to_remove,
)
from pipelines_core.ops.document.delete_many_ref_doc_from_docstore import (
    delete_many_ref_doc_from_docstore,
)
from pipelines_core.ops.nodes.delete_many_nodes_from_vector_store import (
    delete_many_nodes_from_vector_store,
)
from pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.types.RefDocDocument import RefDocDocument


@graph
def delete_removed_ref_docs_from_docstore(
    data_lake_files: List[DataLakeFile],
) -> Output[List[RefDocDocument]]:
    """Deletes documents from the document store and vector store that are no longer present in the Data Lake."""
    return delete_many_nodes_from_vector_store(
        delete_many_ref_doc_from_docstore(fetch_ref_docs_to_remove(data_lake_files))
    )
