from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
async def parse_document_from_data_lake(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Loads and parses the document from data lake storage."""
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    reader_name = reader.__class__.__name__
    context.log.info(f"Using reader {reader_name} for document of type {data_lake_file.filetype}")
    context.log.info(f"Data Lake file uri: {data_lake_file.uri}")
    documents = await reader.aload_data(
        data_lake_file.uri,
        fs=data_lake_file_system,
        include_images=document_parser.include_images,
    )
    document = documents[0]

    ref_doc = RefDocDocument(**document.model_dump())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)
    ref_doc.metadata.update({"document_parser": reader_name})
    return ref_doc
