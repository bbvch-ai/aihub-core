from typing import List

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import OpExecutionContext, op

from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.path_utils import get_container_name, get_document_figures_folder_name


@op(code_version="v1")
def delete_figures_for_many_ref_doc(
    context: OpExecutionContext,
    ref_docs: List[RefDocDocument],
) -> List[RefDocDocument]:
    """Deletes figures associated with each RefDocDocument from the data lake."""
    account_url = "https://aihubdevstchedatalake.blob.core.windows.net"
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    for ref_doc in ref_docs:
        figures_folder = get_document_figures_folder_name(ref_doc.uri)
        container_name = get_container_name(ref_doc.uri)

        container_client = blob_service_client.get_container_client(container_name)
        # add / to avoid including the folder in blobs
        blobs = container_client.list_blobs(name_starts_with=figures_folder + "/")

        for blob in blobs:
            container_client.delete_blob(blob.name)

        # then separately delete the figure folder once all figures have been deleted
        container_client.delete_blob(figures_folder)

    context.log.info(f"All figures were deleted for {len(ref_docs)} documents.")
    return ref_docs
