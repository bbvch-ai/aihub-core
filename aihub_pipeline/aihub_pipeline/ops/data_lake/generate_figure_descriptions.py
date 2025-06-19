import html
from typing import List

from bs4 import BeautifulSoup
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem
from llama_index.core.base.llms.types import ImageBlock, TextBlock
from llama_index.core.llms import LLM
from llama_index.core.prompts import RichPromptTemplate

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(code_version="v1")
def generate_figure_descriptions(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    language_model: ResourceParam[LLM],
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> DocumentWithFigureInfo:
    """Injects image Markdown tags into the document content by replacing HTML figure tags."""

    soup = BeautifulSoup(doc_with_figures.text_resource.text, "html.parser")
    figure_tags = soup.find_all(NODE_CONTENT_TYPE_FIGURE)
    for i, figure_tag in enumerate(figure_tags):
        # 3000 characters of surrounding text, 1500 before and 1500 after the figure tag
        text_before = figure_tag.previous_sibling[-1500:] if figure_tag.previous_sibling else ""
        text_after = figure_tag.next_sibling[:1500] if figure_tag.next_sibling else ""
        context.log.info(f"Found figure tag: {figure_tag.text}")
        figure_path = figure_tag.text.split("](")[1][:-1]
        with data_lake_file_system.open(figure_path) as f:
            figure_bytes = f.read()

        context_blocks = [
            TextBlock(text=text_before),
            ImageBlock(image=figure_bytes),
            TextBlock(text=text_after),
        ]
        figure_description = generate_description(
            language_model=language_model,
            context_blocks=context_blocks,
        )
        markdown_figure = f"![{figure_description}]({figure_path})"
        figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

    doc_with_figures.text_resource.text = html.unescape(str(soup))

    return doc_with_figures


def generate_description(
    language_model: LLM,
    context_blocks: List[TextBlock | ImageBlock],
) -> str:
    """
    Generate a detailed description of an image using a vision model,
    taking into account the surrounding text context from the document.
    """
    t = LocaleHandler(locale="en")
    context_prompt_locale = t("lib.prompt.figure_description_generator.context_string")

    messages = RichPromptTemplate(template_str=context_prompt_locale).format_messages()
    # RichPromptTemplate doesn't support bytes from ImageBlock
    messages[-1].blocks = context_blocks
    response = language_model.chat(messages=messages)
    description = response.message.content.replace("\n", " ")

    return description
