from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
async def parse_document_from_data_lake(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Loads and parses the document from data lake storage."""
    context.log.info(f"Parsing document from data lake file with uri: {data_lake_file.uri}")
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    context.log.info(f"Found reader for filetype {data_lake_file.filetype}")
    reader_name = reader.__class__.__name__
    context.log.info(f"Using reader {reader_name} for document of type {data_lake_file.filetype}")
    context.log.info(f"Data Lake file uri: {data_lake_file.uri}")
    documents = await reader.aload_data(
        data_lake_file.uri,
        fs=data_lake_file_system,
        include_images=document_parser.include_images,
    )
    context.log.info(f"Loaded {len(documents)} documents from data lake file")
    document = documents[0]
    context.log.info(f"Parsed document with id {document.id_}")

    ref_doc = RefDocDocument(**document.model_dump())
    context.log.info(f"Created ref doc with id {ref_doc.id_}")
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)
    context.log.info(f"Added metadata from data lake file to ref doc with id {ref_doc.id_}")
    ref_doc.metadata.update({"document_parser": reader_name})
    context.log.info(f"Updated metadata with document parser name to ref doc with id {ref_doc.id_}")
    return ref_doc
