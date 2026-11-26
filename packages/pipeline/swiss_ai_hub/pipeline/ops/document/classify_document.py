from dagster import OpExecutionContext, Output, op
from openai import APIError

from swiss_ai_hub.pipeline.resources.parser.document_classification_resource import DocumentClassificationResource
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.model_builders import build_language_model, ingestor_config_for_bucket
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v1")
def classify_document(
    context: OpExecutionContext, ref_doc: RefDocDocument, document_classification: DocumentClassificationResource
) -> Output[RefDocDocument]:
    """Classify the document with its knowledge database's text model, if the database asks for it.

    A record synced with frontmatter (Jira, Confluence, MediaWiki) already says what it is through its own fields, the
    only thing that fills `excluded_embed_metadata_keys` before this op, so it is passed through rather than spending a
    model call to learn it is `other`. Classification is an enrichment: a failed call leaves the document unclassified,
    searchable as before and picked up by the next backfill, instead of failing the ingestion of its content. Only the
    model's failures pass; a fault in reading its answer fails the run.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    if not ingestor_config_for_bucket(bucket).with_document_classification:
        context.log.info(f"Document classification is disabled for '{bucket}'; passing the document through.")
        return Output(ref_doc)
    if ref_doc.excluded_embed_metadata_keys:
        context.log.info(f"{ref_doc.uri} is a synced record with its own fields; not classifying it.")
        return Output(ref_doc)

    llm = build_language_model(bucket)
    try:
        answer = document_classification.answer(ref_doc, llm)
    except (APIError, ValueError):
        # The model unreachable or refusing (APIError), or its answer still not fitting the schema after the model's own
        # retries (ValueError, pydantic's ValidationError among them): both pass, and the backfill classifies the
        # document later. Anything else is a fault of this code or its setup and fails the run.
        context.log.warning(f"Classifying {ref_doc.uri} failed; ingesting it unclassified.", exc_info=True)
        return Output(ref_doc)
    classified, classification = document_classification.apply(ref_doc, answer)

    found = [key for key, value in classification.values.items() if value is not None]
    context.log.info(f"Classified {ref_doc.uri} as {classification.document_type} ({len(found)} values).")
    return Output(
        classified,
        metadata={"Document type": classification.document_type.value, "Values found": len(found)},
    )
