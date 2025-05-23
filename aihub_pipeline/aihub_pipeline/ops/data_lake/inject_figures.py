import base64
import re
from typing import Optional

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, op, ResourceParam, RetryPolicy, Backoff
from llama_index.core.base.llms.types import ChatMessage, MessageRole, TextBlock, ImageBlock
from llama_index.core.llms import LLM

from aihub_pipeline.ops.data_lake.process_document_without_figures import process_document_without_figures
from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.types.FigureMetadata import FigureMetadata

system_prompt = """You are an expert at creating high-quality image descriptions for document accessibility.
Your task is to generate detailed alt text for figures in documents that:

1. Concisely describes the visual content (images, charts, diagrams, etc.)
2. Captures the key information being conveyed by the figure
3. For charts and diagrams: describes the structure, identifies axes, data points, and trends
4. For tables: describes the structure and summarizes key data points
5. Extracts any visible text in the image when relevant
6. Uses appropriate technical language while remaining accessible
7. Connects the image description to the surrounding document context
8. Avoids unnecessary verbosity or speculation

Format your descriptions as concise, factual paragraphs that could be used directly as alt text.
Focus on being informative and helping the reader understand what they can't see.
Do **NOT** come up with information, only reference what you can see in the iamge.
Write your reply in the SAME language as the context text and image text."""


@op(code_version="v2", retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL))
def inject_figures(
    context: OpExecutionContext,
    doc_with_figures: DocumentWithFigureInfo,
    figure_metadata: FigureMetadata,
    language_model: ResourceParam[LLM],
    data_lake_client: ResourceParam[FileSystemClient],
) -> DocumentWithFigureInfo:
    """
    Injects image Markdown tags into the document content by replacing HTML figure tags.
    """
    if not figure_metadata.figure_paths:
        context.log.info("No figures found, skipping injection")
        doc_with_figures = process_document_without_figures(doc_with_figures)
        return doc_with_figures

    # Pattern to match HTML figure tags
    figure_pattern = r"<figure>.*?</figure>"

    updated_content = doc_with_figures.text_resource.text
    figures_replaced = 0

    # Loop through each figure path
    for i, (image_path, image_url) in enumerate(zip(figure_metadata.figure_paths, figure_metadata.figure_urls)):
        # Search for the next figure tag
        match = re.search(figure_pattern, updated_content, re.DOTALL)

        if not match:
            if figures_replaced == 0:
                context.log.warning("No figure tags found in document content")
            else:
                context.log.warning(f"No more figure tags found after replacing {figures_replaced} figures")
            break

        # Get the matched figure tag's span (start and end positions)
        start, end = match.span()

        # Extract surrounding text for context (up to 1000 characters before and after)
        # Adjust the context window size as needed
        context_window = 1000
        text_before = updated_content[max(0, start - context_window) : start]
        text_after = updated_content[end : min(len(updated_content), end + context_window)]

        # Extract paragraphs for better context
        # Look for natural paragraph breaks or sentence boundaries
        def extract_paragraphs(text, max_paragraphs=2):
            # Split by double newlines (typical paragraph separator)
            paragraphs = re.split(r"\n\n+", text)
            # If no paragraph breaks, try to split by sentences
            if len(paragraphs) <= 1:
                paragraphs = re.split(r"(?<=[.!?])\s+", text)

            # Return the last few paragraphs for text_before or first few for text_after
            if text == text_before:
                return " ".join(paragraphs[-max_paragraphs:])
            else:
                return " ".join(paragraphs[:max_paragraphs])

        # Get the most relevant text from before and after
        refined_before = extract_paragraphs(text_before)
        refined_after = extract_paragraphs(text_after)

        # Combine the context
        surrounding_text = f"{refined_before}\n\n[IMAGE LOCATION]\n\n{refined_after}"

        # Try to generate a description if we have blob service client
        description = "Image"
        try:
            # Download the image
            blob_client = data_lake_client.get_file_client(image_path)
            image_bytes = blob_client.download_file().readall()

            # Generate description with context
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

        # Create markdown image tag with description
        markdown_image = f"![{description}]({image_url})"

        # Replace the figure tag with the markdown image using the exact span positions
        updated_content = updated_content[:start] + markdown_image + updated_content[end:]
        figures_replaced += 1

    # Update the document content
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
        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Prepare user prompt with surrounding text context if available
        user_text = (
            "Please provide a detailed, accurate description of this image that would serve as effective alt text."
        )

        if surrounding_text:
            user_text += f"\n\nContext from the document surrounding this image:\n\n{surrounding_text}"

        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                blocks=[
                    TextBlock(text=user_text),
                    ImageBlock(image=base64_image),
                ],
            ),
            ChatMessage(
                role=MessageRole.USER,
                blocks=[
                    TextBlock(text=user_text),
                    ImageBlock(image=base64_image),
                ],
            ),
        ]

        response = language_model.chat(messages=messages)

        # make it a single paragraph
        description = response.message.content.replace("\n", " ")

        return description

    except Exception as e:
        context.log.error(f"Failed to generate image description: {str(e)}")
        return f"Figure {figure_index + 1}"
