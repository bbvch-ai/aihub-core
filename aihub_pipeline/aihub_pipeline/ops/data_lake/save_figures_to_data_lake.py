from typing import List, Optional

from bs4 import BeautifulSoup
from dagster import ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata
from aihub_pipeline.util.path_utils import create_data_lake_figures_folder_name


@op(code_version="v1")
def save_figures_to_data_lake(
    doc_with_figures: DocumentWithFigureInfo,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    data_lake_resource: ResourceParam[DataLakeResource],
) -> Optional[List[FigureMetadata]]:
    """Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient."""

    figures_metadata = []
    figures_dir = create_data_lake_figures_folder_name(data_lake_file.uri, data_lake_resource.figures_directory_name)

    soup = BeautifulSoup(doc_with_figures.text_resource.text, "html.parser")
    figure_tags = soup.find_all("figure")

    for idx, figure_tag in enumerate(figure_tags):
        figure_str = figure_tag.text.split("](")[1][:-1]
        figure_str = figure_str.split("data:image/png;base64,")[1]
        blob_path = f"{figures_dir}/figure_{idx + 1}.png"

        with data_lake_file_system.open(blob_path, mode="wb") as f:
            f.write(figure_str.encode("utf-8"))

        figures_metadata.append(FigureMetadata(figure_path=blob_path))

        markdown_figure = f"![Figure {idx + 1}](url)"
        figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

    return figures_metadata
