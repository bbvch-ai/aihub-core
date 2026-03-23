from dagster import Output, graph

from swiss_ai_hub.pipeline.ops.data_lake.fetch_ref_docs_to_remove import fetch_ref_docs_to_remove
from swiss_ai_hub.pipeline.ops.document.delete_figures_for_many_ref_doc import delete_figures_for_many_ref_doc
from swiss_ai_hub.pipeline.ops.document.delete_many_ref_doc_from_docstore import delete_many_ref_doc_from_docstore
from swiss_ai_hub.pipeline.ops.nodes.delete_many_nodes_from_vector_store import delete_many_nodes_from_vector_store
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@graph
def delete_removed_ref_docs_from_docstore(
    data_lake_files: list[DataLakeFile],
) -> Output[list[RefDocDocument]]:
    """Deletes documents from the document store and vector store that are no longer present in the Data Lake."""
    return delete_many_nodes_from_vector_store(
        delete_figures_for_many_ref_doc(delete_many_ref_doc_from_docstore(fetch_ref_docs_to_remove(data_lake_files)))
    )
