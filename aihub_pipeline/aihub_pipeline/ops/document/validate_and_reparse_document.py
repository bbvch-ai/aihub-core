"""Op for validating parsed documents and triggering re-parse on severe bugs."""

import json

from aihub_lib.generative_ai.document.refinement import validate_document_quality
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument

QUALITY_VALIDATION_METADATA_KEY = "quality_validation"


@op(code_version="v1")
async def validate_and_reparse_document(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Validate parsed document for severe parsing bugs and re-parse if needed.

    This op detects parsing failures like:
    - Excessive text repetition (parser stuck in loop)
    - Severe encoding failures

    If a bug is detected, the document is re-parsed with different settings.
    Normal OCR errors are NOT flagged - those are handled by text refinement.
    """
    validation_result = validate_document_quality(ref_doc.text)

    # Store validation metadata as JSON string (Dagster metadata only accepts primitives)
    updated_metadata = {**ref_doc.metadata} if ref_doc.metadata else {}
    updated_metadata[QUALITY_VALIDATION_METADATA_KEY] = json.dumps(validation_result.model_dump())

    if validation_result.validation_skipped:
        context.log.info(f"Quality validation skipped: {validation_result.message}")
        return RefDocDocument(
            text=ref_doc.text,
            extra_info=ref_doc.extra_info,
            metadata=updated_metadata,
            id_=ref_doc.id_,
        )

    if validation_result.is_valid:
        context.log.info(f"Document passed quality validation: {validation_result.message}")
        return RefDocDocument(
            text=ref_doc.text,
            extra_info=ref_doc.extra_info,
            metadata=updated_metadata,
            id_=ref_doc.id_,
        )

    # Document failed validation - attempt re-parse
    context.log.warning(f"Document failed quality validation: {validation_result.message}")
    context.log.info("Attempting re-parse with alternative settings...")

    reparsed_doc = await _reparse_document(
        context=context,
        data_lake_file=data_lake_file,
        data_lake_file_system=data_lake_file_system,
        document_parser=document_parser,
    )

    # Validate the re-parsed document
    reparse_validation = validate_document_quality(reparsed_doc.text)
    updated_metadata["reparse_validation"] = json.dumps(reparse_validation.model_dump())
    updated_metadata["was_reparsed"] = True

    if reparse_validation.is_valid:
        context.log.info("Re-parsed document passed quality validation")
        return RefDocDocument(
            text=reparsed_doc.text,
            extra_info=reparsed_doc.extra_info,
            metadata=updated_metadata,
            id_=ref_doc.id_,
        )

    # Re-parse also failed - log warning but continue with original
    # (downstream processing may still extract some value)
    context.log.error(
        f"Re-parsed document also failed validation: {reparse_validation.message}. "
        "Continuing with original document - manual review recommended."
    )
    updated_metadata["reparse_failed"] = True
    return RefDocDocument(
        text=ref_doc.text,
        extra_info=ref_doc.extra_info,
        metadata=updated_metadata,
        id_=ref_doc.id_,
    )


async def _reparse_document(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: AbstractFileSystem,
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Re-parse a document with alternative settings.

    Currently uses the same parser but future versions could:
    - Try different VLM models
    - Use different parsing pipelines (e.g., standard vs VLM)
    - Adjust timeout/retry settings
    """
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
    reader_name = reader.__class__.__name__

    context.log.info(f"Re-parsing with {reader_name} (include_images={document_parser.include_images})")

    documents = await reader.aload_data(
        data_lake_file.uri,
        fs=data_lake_file_system,
        include_images=document_parser.include_images,
    )
    document = documents[0]

    ref_doc = RefDocDocument(**document.model_dump())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)
    ref_doc.metadata.update({"document_parser": reader_name, "is_reparse": True})

    return ref_doc
