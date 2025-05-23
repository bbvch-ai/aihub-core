from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, op, ResourceParam
from fsspec import AbstractFileSystem

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata
from aihub_pipeline.util.path_utils import get_document_figures_folder_name


@op(code_version="v1")
def save_figures_to_data_lake(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    data_lake_file: DataLakeFile,
    data_lake_client: ResourceParam[FileSystemClient],
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> FigureMetadata:
    """
    Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient.
    """
    if doc_with_figures.operation_id is None and len(doc_with_figures.figure_ids) < 1:
        context.log.info("No figures found, skip saving to data lake.")
        return FigureMetadata(figure_paths=None, figure_urls=None, container_name=None)

    document_intelligence_client = DocumentIntelligenceAccess().get_client()
    figure_paths, figure_urls = [], []
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
            with data_lake_file_system.open(blob_path, mode="wb") as f:
                f.write(response_bytes)

            file_client = data_lake_client.get_file_client(blob_path)

            figure_paths.append(blob_path)
            figure_urls.append(file_client.url)

        except Exception as e:
            context.log.error(f"Failed to save figure {idx + 1}: {str(e)}\n\n with path {blob_path}")
            # Log the full exception for debugging
            context.log.error(f"Exception details: {type(e).__name__}: {str(e)}")

    metadata = FigureMetadata(figure_paths=figure_paths, figure_urls=figure_urls)
    return metadata
