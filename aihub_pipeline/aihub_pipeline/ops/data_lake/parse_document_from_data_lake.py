from dagster import op, OpExecutionContext, ResourceParam
from fsspec import AbstractFileSystem

from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(code_version="v1")
def parse_document_from_data_lake(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> DocumentWithFigureInfo:
    """Loads and parses the document from data lake storage"""
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)

    context.log.info(f"Using reader {reader.__class__.__name__} for document of type {data_lake_file.filetype}")

    documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
    document = documents[0]

    # Create a DocumentWithFigureInfo
    doc = DocumentWithFigureInfo(**document.dict())

    return doc
