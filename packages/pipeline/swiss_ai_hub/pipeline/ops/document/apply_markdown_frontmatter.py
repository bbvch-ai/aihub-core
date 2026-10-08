from dagster import MetadataValue, OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.types.malformed_frontmatter_error import MalformedFrontmatterError
from swiss_ai_hub.pipeline.types.markdown_frontmatter import MarkdownFrontmatter
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
def apply_markdown_frontmatter(context: OpExecutionContext, ref_doc: RefDocDocument) -> Output[RefDocDocument]:
    """Move a markdown file's frontmatter out of the text and into the document's fields and metadata.

    Only `.md` files are read: other parsers emit markdown too, and a converted file that opens with a horizontal rule
    must not be taken for YAML. A broken block never fails ingestion; the file is ingested as written.
    """
    if not ref_doc.uri.lower().endswith(".md"):
        return Output(ref_doc)

    try:
        frontmatter = MarkdownFrontmatter.from_markdown(ref_doc.text)
    except MalformedFrontmatterError as malformed:
        context.log.warning(f"{malformed}. Ingesting {ref_doc.uri} as plain text.")
        return Output(ref_doc)

    if frontmatter is None:
        return Output(ref_doc)

    for raw_key, reason in frontmatter.skipped.items():
        context.log.warning(f"Frontmatter key '{raw_key}' of {ref_doc.uri} is skipped: {reason}")

    return Output(
        ref_doc.with_frontmatter(frontmatter),
        metadata={
            "Frontmatter metadata keys": MetadataValue.json(sorted(frontmatter.metadata)),
            "Skipped frontmatter keys": MetadataValue.json(frontmatter.skipped),
        },
    )
