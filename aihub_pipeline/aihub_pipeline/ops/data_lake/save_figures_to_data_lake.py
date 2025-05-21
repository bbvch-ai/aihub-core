from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import OpExecutionContext, op

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata
from aihub_pipeline.util.path_utils import get_container_name, get_document_figures_folder_name


@op(code_version="v1")
def save_figures_to_data_lake(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    data_lake_file: DataLakeFile,
) -> FigureMetadata:
    """
    Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient.
    """
    if doc_with_figures.operation_id is None and len(doc_with_figures.figure_ids) < 1:
        context.log.info("No figures found, skip saving to data lake.")
        return FigureMetadata(figure_paths=None, figure_urls=None, container_name=None)

    document_intelligence_client = DocumentIntelligenceAccess().get_client()
    figure_paths, figure_urls = [], []
    account_url = "https://aihubdevstchedatalake.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    container_name = get_container_name(data_lake_file.uri)
    figures_dir = get_document_figures_folder_name(data_lake_file.uri)

    context.log.info(f"Saving {len(doc_with_figures.figure_ids)} figures to {figures_dir}")

    for idx, figure_id in enumerate(doc_with_figures.figure_ids):
        try:
            # Get the raw figure data using the specified approach
            response = document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=doc_with_figures.operation_id,
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

    metadata = FigureMetadata(figure_paths=figure_paths, figure_urls=figure_urls, container_name=container_name)
    return metadata
