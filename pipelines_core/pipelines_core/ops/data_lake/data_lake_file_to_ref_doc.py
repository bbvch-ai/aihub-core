from dagster import op, ResourceParam, OpExecutionContext
from fsspec import AbstractFileSystem

from pipelines_core.pipelines_core.resources.parser.DocumentParserResource import DocumentParserResource
from pipelines_core.pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.pipelines_core.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def data_lake_file_to_ref_doc(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Loads the data lake file using the data lake file system, parses the file using the parser, returns the
    parsed document as a RefDocDocument with adding all metadata from the data lake to the RefDocDocument.
    """
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)

    context.log.info(f"Using reader {reader.__class__.__name__} for document of type {data_lake_file.filetype}")

    documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
    document = documents[0]

    ref_doc = RefDocDocument(**document.dict())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)

    return ref_doc
