import html
import json

from bs4 import BeautifulSoup
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem
from llama_index.core.base.llms.types import ImageBlock, TextBlock
from llama_index.core.llms import LLM
from llama_index.core.prompts import RichPromptTemplate
from openai import BadRequestError
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.model_builders import build_language_model
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v1")
def generate_figure_descriptions(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> RefDocDocument:
    """Injects image Markdown tags into the document content by replacing HTML figure tags."""
    language_model = build_language_model(bucket_from_partition_key(context.partition_key))

    if ref_doc.text_resource is None:
        context.log.warning(f"Document has no text content, skipping figure description generation: {ref_doc.id_}")
        return ref_doc

    soup = BeautifulSoup(ref_doc.text_resource.text, "html.parser")
    figure_tags = soup.find_all(NODE_CONTENT_TYPE_FIGURE)
    for i, figure_tag in enumerate(figure_tags):
        # 3000 characters of surrounding text, 1500 before and 1500 after the figure tag
        text_before = figure_tag.previous_sibling[-1500:] if figure_tag.previous_sibling else ""
        text_after = figure_tag.next_sibling[:1500] if figure_tag.next_sibling else ""
        figure_path = figure_tag.text.split("](")[1][:-1]
        with data_lake_file_system.open(figure_path) as f:
            figure_bytes = f.read()

        figure_description = generate_description(
            language_model=language_model,
            image_block=ImageBlock(image=figure_bytes),
            before_text_block=TextBlock(text=text_before),
            after_text_block=TextBlock(text=text_after),
            context=context,
        )
        markdown_figure = f"![{figure_description}]({figure_path})"
        figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

    ref_doc.text_resource.text = html.unescape(str(soup))

    return ref_doc


def generate_description(
    language_model: LLM,
    image_block: ImageBlock,
    before_text_block: TextBlock = None,
    after_text_block: TextBlock = None,
    context: OpExecutionContext = None,
) -> str:
    """
    Generate a detailed description of an image using a vision model,
    taking into account the surrounding text context from the document.
    """
    # TODO detect language of the document
    t = LocaleHandler()
    context_prompt_locale = t("lib.prompt.figure_description_generator.context_string")

    try:
        messages = RichPromptTemplate(template_str=context_prompt_locale).format_messages()
        # RichPromptTemplate doesn't support bytes from ImageBlock
        context_blocks = [block for block in [before_text_block, image_block, after_text_block] if block]
        messages[-1].blocks.extend(context_blocks)
        response = language_model.chat(messages=messages)
        description = response.message.content.replace("\n", " ")

        return description
    except BadRequestError as e:
        # We do not want to fail the entire document processing if this happens.
        # We try to generate the description again without the surrounding text.
        # If this fails, we use an empty string as a fallback.
        # However, we should monitor this issue.
        if context:
            context.log.warning(f"BadRequestError caught. It might be a content filter issue. Error: {e}")
            try:
                error_details = e.response.json()
                inner_error = error_details.get("error", {}).get("inner_error", {})
                if filter_results := inner_error.get("content_filter_results"):
                    context.log.warning(f"Azure content filter results: {json.dumps(filter_results, indent=2)}")
            except (json.JSONDecodeError, AttributeError):
                context.log.warning("Could not parse detailed error response from BadRequestError.")

        if before_text_block or after_text_block:
            context.log.info("Attempting to generate description again without surrounding text.")
            try:
                return generate_description(
                    language_model=language_model,
                    image_block=image_block,
                    context=context,
                    before_text_block=None,
                    after_text_block=None,
                )
            except Exception as retry_e:
                context.log.error(f"Retry attempt also failed: {retry_e}", exc_info=True)
                return ""  # If retry fails, return empty string.

        return ""  # If there was no surrounding text to remove, we can't retry.
