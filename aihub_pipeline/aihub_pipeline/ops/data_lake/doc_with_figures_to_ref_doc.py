from dagster import op

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def doc_with_figures_to_ref_doc(
    data_lake_file: DataLakeFile,
    doc_with_figures: DocumentWithFigureInfo,
) -> RefDocDocument:
    """Turns a DocumentWithFigureInfo into a RefDocDocument."""

    ref_doc = RefDocDocument(**doc_with_figures.model_dump())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)

    return ref_doc
