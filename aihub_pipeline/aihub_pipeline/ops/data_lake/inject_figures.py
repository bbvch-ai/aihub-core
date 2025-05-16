import base64
import os
import re
from typing import List, Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import OpExecutionContext
from openai import AzureOpenAI

from aihub_pipeline.types.RefDocDocument import RefDocDocument


def inject_figures(
    context: OpExecutionContext,
    document: RefDocDocument,
    container_name: str,
    figure_paths: List[str],
    figure_urls: List[str],
) -> RefDocDocument:
    """Injects image Markdown tags into the document content by replacing HTML figure tags.

    This operation:
    1. Looks for HTML figure tags in the document content using re.search
    2. Extracts surrounding text to provide context for image description
    3. Generates detailed descriptions using GPT-4o with document context
    4. Replaces each figure tag with a markdown image tag using the saved image URLs
    5. Uses match.span() to ensure the exact tag is replaced

    Returns the document with updated content containing markdown image tags.
    """
    if not figure_paths:
        context.log.info("No figures found, skipping injection")
        return document

    # Pattern to match HTML figure tags
    figure_pattern = r"<figure>.*?</figure>"

    # Get blob service client to download images for description generation
    try:
        account_url = "https://aihubdevstchedatalake.blob.core.windows.net"
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    except Exception as e:
        context.log.error(f"Failed to create BlobServiceClient: {str(e)}")
        return document

    # Start with the original content
    updated_content = document.text_resource.text
    figures_replaced = 0

    # Loop through each figure path
    for i, (image_path, image_url) in enumerate(zip(figure_paths, figure_urls)):
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
        if blob_service_client:
            try:
                # Download the image
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=image_path)
                image_data = blob_client.download_blob().readall()

                # Generate description with context
                description = generate_description(
                    context, image_data, figure_index=i, surrounding_text=surrounding_text
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
    document.text_resource.text = updated_content
    context.log.info(f"Updated document content with {figures_replaced} markdown image with contextual descriptions.")

    return document


def generate_description(
    context: OpExecutionContext,
    image_bytes: bytes,
    figure_index: int,
    surrounding_text: Optional[str] = None,
) -> str:
    """
    Generate a detailed description of an image using the GPT-4o vision model,
    taking into account the surrounding text context from the document.

    Args:
        context: The operation execution context for logging
        image_bytes: The raw image data as bytes
        figure_index: The index of the figure within the document
        surrounding_text: Text surrounding the image in the document, providing context

    Returns:
        A detailed description of the image
    """
    try:
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")

        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Create a robust system prompt
        # TODO detect document language and localize prompt
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
Do **NOT** come up with information, only reference what you can see in the iamge."""

        # Prepare user prompt with surrounding text context if available
        user_text = (
            "Please provide a detailed, accurate description of this image that would serve as effective alt text."
        )

        if surrounding_text:
            user_text += f"\n\nContext from the document surrounding this image:\n\n{surrounding_text}"

        endpoint = "https://aihub-dev-openai-che.openai.azure.com/"
        deployment = "gpt-4o"

        api_version = "2024-12-01-preview"

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                    ],
                },
            ],
            max_tokens=500,
            temperature=0.0,
            model=deployment,
        )

        # Parse the response
        return response.choices[0].message.content

    except Exception as e:
        context.log.error(f"Failed to generate image description: {str(e)}")
        return f"Figure {figure_index + 1}"
