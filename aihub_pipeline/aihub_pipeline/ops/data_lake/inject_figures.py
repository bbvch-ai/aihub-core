import re
from typing import Optional

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, op, ResourceParam, RetryPolicy, Backoff
from llama_index.core.base.llms.types import ChatMessage, MessageRole, TextBlock, ImageBlock
from llama_index.core.llms import LLM

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_pipeline.ops.data_lake.process_document_without_figures import process_document_without_figures
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata

system_prompt = """"""


@op(code_version="v2", retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL))
def inject_figures(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    figure_metadata: FigureMetadata,
    language_model: ResourceParam[LLM],
    data_lake_client: ResourceParam[FileSystemClient],
) -> DocumentWithFigureInfo:
    """Injects image Markdown tags into the document content by replacing HTML figure tags."""
    if not figure_metadata.figure_paths:
        context.log.info("No figures found, skipping injection")
        doc_with_figures = process_document_without_figures(doc_with_figures)
        return doc_with_figures

    figure_pattern = r"<figure>.*?</figure>"

    updated_content = doc_with_figures.text_resource.text
    figures_replaced = 0

    for i, (image_path, image_url) in enumerate(zip(figure_metadata.figure_paths, figure_metadata.figure_urls)):

        match = re.search(figure_pattern, updated_content, re.DOTALL)

        if not match:
            if figures_replaced == 0:
                context.log.warning("No figure tags found in document content")
            else:
                context.log.warning(f"No more figure tags found after replacing {figures_replaced} figures")
            break

        start, end = match.span()

        context_window = 1000
        text_before = updated_content[max(0, start - context_window) : start]
        text_after = updated_content[end : min(len(updated_content), end + context_window)]

        def extract_paragraphs(text, max_paragraphs=2):

            paragraphs = re.split(r"\n\n+", text)

            if len(paragraphs) <= 1:
                paragraphs = re.split(r"(?<=[.!?])\s+", text)

            if text == text_before:
                return " ".join(paragraphs[-max_paragraphs:])
            else:
                return " ".join(paragraphs[:max_paragraphs])

        refined_before = extract_paragraphs(text_before)
        refined_after = extract_paragraphs(text_after)

        surrounding_text = f"{refined_before}\n\n[IMAGE LOCATION]\n\n{refined_after}"

        try:
            blob_client = data_lake_client.get_file_client(image_path)
            image_bytes = blob_client.download_file().readall()

            description = generate_description(
                context=context,
                language_model=language_model,
                image_bytes=image_bytes,
                figure_index=i,
                surrounding_text=surrounding_text,
            )
        except Exception as e:
            context.log.error(f"Error processing image {i+1} for description: {str(e)}")
            description = f"Figure {i+1}"

        markdown_image = f"![{description}]({image_url})"

        updated_content = updated_content[:start] + markdown_image + updated_content[end:]
        figures_replaced += 1

    doc_with_figures.text_resource.text = updated_content
    context.log.info(f"Updated document content with {figures_replaced} markdown image with contextual descriptions.")

    return doc_with_figures


def generate_description(
    context: OpExecutionContext,
    language_model: LLM,
    image_bytes: bytes,
    figure_index: int,
    surrounding_text: Optional[str] = None,
) -> str:
    """
    Generate a detailed description of an image using the GPT-4o vision model,
    taking into account the surrounding text context from the document.
    """
    try:
        locale_handler = LocaleHandler(locale="en")
        system_prompt = locale_handler("lib.prompt.describer.describe")
        user_text = locale_handler("lib.prompt.describer.user_text")

        if surrounding_text:
            user_text += f"\n\n{locale_handler('lib.prompt.describer.surrounding_text')}\n\n{surrounding_text}"

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

    except Exception as e:
        context.log.error(f"Failed to generate image description: {str(e)}")
        return f"Figure {figure_index + 1}"
