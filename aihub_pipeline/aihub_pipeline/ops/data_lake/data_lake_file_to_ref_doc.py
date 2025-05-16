from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_pipeline.ops.data_lake.inject_figures import inject_figures
from aihub_pipeline.ops.data_lake.reformat_tables import reformat_tables
from aihub_pipeline.ops.data_lake.save_figures_to_data_lake import save_figures_to_data_lake
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def data_lake_file_to_ref_doc(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Loads the data lake file using the data lake file system, parses the file using the parser, returns the
    parsed document as a RefDocDocument with adding all metadata from the data lake to the RefDocDocument.
    Also extracts and saves any figures to the data lake.
    """
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)

    context.log.info(f"Using reader {reader.__class__.__name__} for document of type {data_lake_file.filetype}")

    documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
    document = documents[0]

    ref_doc = RefDocDocument(**document.dict())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)

    # Process and save figures if operation_id exists
    if "operation_id" in document.extra_info and len(document.extra_info["figure_ids"]) > 0:
        document_intelligence_client = DocumentIntelligenceAccess().get_client()
        operation_id = document.extra_info["operation_id"]
        figure_ids = document.extra_info["figure_ids"]

        # Extract and save raw figure data
        saved_figures_paths, saved_figures_urls, container_name = save_figures_to_data_lake(
            context, figure_ids, operation_id, document_intelligence_client, data_lake_file
        )

        ref_doc = inject_figures(context, ref_doc, container_name, saved_figures_paths, saved_figures_urls)

        # Remove the operation_id from metadata
        if "operation_id" in ref_doc.metadata:
            del ref_doc.metadata["operation_id"]
            del ref_doc.metadata["figure_ids"]

    else:
        context.log.info("No figures were detected.")

    ref_doc = reformat_tables(context, ref_doc)
    return ref_doc
