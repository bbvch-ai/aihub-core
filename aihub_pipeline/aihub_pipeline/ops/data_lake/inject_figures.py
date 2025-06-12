from typing import List, Optional

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from bs4 import BeautifulSoup
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock
from llama_index.core.llms import LLM

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata


@op(code_version="v1")
def inject_figures(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    figures_metadata: Optional[List[FigureMetadata]],
    language_model: ResourceParam[LLM],
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> DocumentWithFigureInfo:
    """Injects image Markdown tags into the document content by replacing HTML figure tags."""
    if not figures_metadata:
        context.log.info("No figures found, skipping injection")
        return doc_with_figures

    soup = BeautifulSoup(doc_with_figures.text_resource.text, "html.parser")
    figure_tags = soup.find_all("figure")

    if len(figure_tags) != len(figures_metadata):
        context.log.error(
            f"Mismatch between figure tags ({len(figure_tags)}) and figure metadata ({len(figures_metadata)})"
        )

    for i, (figure_tag, figure_metadata) in enumerate(zip(figure_tags, figures_metadata)):
        # 3000 characters of surrounding text, 1500 before and 1500 after the figure tag
        text_before = figure_tag.previous_sibling[-1500:] if figure_tag.previous_sibling else ""
        text_after = figure_tag.next_sibling[:1500] if figure_tag.next_sibling else ""
        surrounding_text = f"{text_before}\n\n[IMAGE LOCATION]\n\n{text_after}"

        context.log.info(f"Trying to load figure with path: {figure_metadata.figure_path}")
        with data_lake_file_system.open(figure_metadata.figure_path) as f:
            image_bytes = f.read()

        figure_description = generate_description(
            language_model=language_model,
            image_bytes=image_bytes,
            surrounding_text=surrounding_text,
        )
        markdown_figure = f"![{figure_description}]({figure_metadata.figure_path})"
        figure_tag.replace_with(f"<figure>{markdown_figure}</figure>")

    doc_with_figures.text_resource.text = str(soup)

    return doc_with_figures


def generate_description(
    language_model: LLM,
    image_bytes: bytes,
    surrounding_text: Optional[str] = None,
) -> str:
    """
    Generate a detailed description of an image using a vision model,
    taking into account the surrounding text context from the document.
    """
    locale_handler = LocaleHandler(locale="en")
    system_prompt = locale_handler("lib.prompt.figure_description_generator.system_prompt")
    user_text = locale_handler("lib.prompt.figure_description_generator.user_text_instruction")

    if surrounding_text:
        user_text += f"\n\n{locale_handler('lib.prompt.figure_description_generator.surrounding_text_instruction')}\n\n{surrounding_text}"

    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt,
        ),
        ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=user_text),
                ImageBlock(image=image_bytes),
            ],
        ),
    ]

    response = language_model.chat(messages=messages)
    description = response.message.content.replace("\n", " ")

    return description
