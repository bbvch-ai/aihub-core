import html
import json
from collections.abc import Iterable

from bs4 import BeautifulSoup, PageElement, Tag
from bs4.element import PreformattedString
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem
from llama_index.core.base.llms.types import ImageBlock, TextBlock
from llama_index.core.llms import LLM
from llama_index.core.prompts import RichPromptTemplate
from openai import BadRequestError
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.model_builders import build_vision_model, ingestor_config_for_bucket
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key

_CONTEXT_CHARACTERS = 1500


@op(code_version="v3")
def generate_figure_descriptions(
    context: OpExecutionContext,
    ref_doc: RefDocDocument,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> RefDocDocument:
    """Fills each HTML figure tag with an image Markdown tag that carries the figure's description.

    Described with the knowledge database's own vision model (its text model unless it chose one), and only if the
    database asks for figure descriptions at all. A figure's context stops at the neighbouring figure, at a tag holding
    one, or at a page break, so the model reads the text that belongs to this figure and never another figure's
    description.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    if not ingestor_config_for_bucket(bucket).with_figure_descriptions:
        context.log.info(f"Figure descriptions are disabled for '{bucket}'; passing the document through.")
        return ref_doc
    language_model = build_vision_model(bucket)

    if ref_doc.text_resource is None:
        context.log.warning(f"Document has no text content, skipping figure description generation: {ref_doc.id_}")
        return ref_doc

    soup = BeautifulSoup(ref_doc.text_resource.text, "html.parser")
    figure_tags = soup.find_all(NODE_CONTENT_TYPE_FIGURE)
    for figure_tag in figure_tags:
        text_before = _text_before(figure_tag)
        text_after = _text_after(figure_tag)
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
        figure_tag.string = markdown_figure

    ref_doc.text_resource.text = html.unescape(str(soup))

    return ref_doc


def _text_before(figure_tag: Tag) -> str:
    return "".join(reversed(_texts_up_to_boundary(figure_tag.previous_siblings)))[-_CONTEXT_CHARACTERS:].strip()


def _text_after(figure_tag: Tag) -> str:
    return "".join(_texts_up_to_boundary(figure_tag.next_siblings))[:_CONTEXT_CHARACTERS].strip()


def _texts_up_to_boundary(siblings: Iterable[PageElement]) -> list[str]:
    texts: list[str] = []
    collected_characters = 0
    for sibling in siblings:
        if collected_characters >= _CONTEXT_CHARACTERS or _is_boundary(sibling):
            break
        text = _plain_text(sibling)
        texts.append(text)
        collected_characters += len(text)
    return texts


def _is_boundary(element: PageElement) -> bool:
    """A tag holding a figure counts too: html.parser nests the rest of the document in an unclosed `<https://…>`."""
    return isinstance(element, PreformattedString) or (
        isinstance(element, Tag)
        and (element.name == NODE_CONTENT_TYPE_FIGURE or element.find(NODE_CONTENT_TYPE_FIGURE) is not None)
    )


def _plain_text(element: PageElement) -> str:
    """Pads a tag's text with spaces so that words on either side of a `<br>` or a table do not run together."""
    if isinstance(element, Tag):
        return f" {element.get_text(' ', strip=True)} "
    return str(element)


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
