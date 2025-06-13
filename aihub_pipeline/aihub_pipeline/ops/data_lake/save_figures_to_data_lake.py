from typing import List, Optional

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import DocumentIntelligenceLoader
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata
from aihub_pipeline.util.path_utils import create_data_lake_figures_folder_name


@op(code_version="v1")
def save_figures_to_data_lake(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    data_lake_file: DataLakeFile,
    data_lake_client: ResourceParam[FileSystemClient],
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    data_lake_resource: ResourceParam[DataLakeResource],
    document_parser: ResourceParam[DocumentParserResource],
) -> Optional[List[FigureMetadata]]:
    """Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient."""
    if len(doc_with_figures.figure_ids) < 1:
        context.log.info("No figures found, skip saving to data lake.")
        return None

    reader: DocumentIntelligenceLoader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    figures_metadata = []
    figures_dir = create_data_lake_figures_folder_name(data_lake_file.uri, data_lake_resource.figures_directory_name)

    context.log.info(f"Saving {len(doc_with_figures.figure_ids)} figures to {figures_dir}")

    for idx, figure_id in enumerate(doc_with_figures.figure_ids):
        response = reader.document_intelligence_client.get_analyze_result_figure(
            model_id="prebuilt-layout",
            result_id=doc_with_figures.operation_id,
            figure_id=figure_id,
        )

        blob_path = f"{figures_dir}/figure_{idx + 1}.png"
        with data_lake_file_system.open(blob_path, mode="wb") as f:
            for chunk in response:
                f.write(chunk)

        figures_metadata.append(FigureMetadata(figure_path=blob_path))

    return figures_metadata
