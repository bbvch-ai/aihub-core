from dagster import op

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def doc_with_figures_to_ref_doc(
    data_lake_file: DataLakeFile,
    doc_with_figures: DocumentWithFigureInfo,
) -> RefDocDocument:
    """Loads the data lake file using the data lake file system, parses the file using the parser, returns the
    parsed document as a RefDocDocument with adding all metadata from the data lake to the RefDocDocument.
    Also extracts and saves any figures to the data lake.
    """

    ref_doc = RefDocDocument(**doc_with_figures.dict())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)

    return ref_doc
