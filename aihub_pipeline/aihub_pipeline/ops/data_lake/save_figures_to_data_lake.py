from typing import List

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import OpExecutionContext

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.util.path_utils import get_container_name, get_document_figures_folder_name


def save_figures_to_data_lake(
    context: OpExecutionContext,
    figure_ids: List[str],
    operation_id: str,
    document_intelligence_client,
    data_lake_file: DataLakeFile,
) -> tuple:
    """
    Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient.

    Args:
        context: The operation execution context
        figure_ids: List of figure_ids from the document intelligence result
        operation_id: The operation ID for retrieving figure data
        document_intelligence_client: The document intelligence client
        data_lake_file: The source data lake file

    Returns:
        List of paths to the saved figures
    """
    figure_paths, figure_urls = [], []
    account_url = "https://aihubdevstchedatalake.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    container_name = get_container_name(data_lake_file.uri)
    figures_dir = get_document_figures_folder_name(data_lake_file.uri)

    context.log.info(f"Saving {len(figure_ids)} figures to {figures_dir}")

    for idx, figure_id in enumerate(figure_ids):
        try:
            # Get the raw figure data using the specified approach
            response = document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=operation_id,
                figure_id=figure_id,
            )

            # Combine all chunks of the response
            response_bytes = bytes()
            for chunk in response:
                response_bytes += chunk

            blob_path = f"{figures_dir}/figure_{idx + 1}.png"
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
            blob_client.upload_blob(response_bytes)

            figure_paths.append(blob_path)
            figure_urls.append(blob_client.url)

        except Exception as e:
            context.log.error(f"Failed to save figure {idx + 1}: {str(e)}")
            # Log the full exception for debugging
            context.log.error(f"Exception details: {type(e).__name__}: {str(e)}")

    return figure_paths, figure_urls, container_name
