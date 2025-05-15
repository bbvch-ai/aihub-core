import base64
import os
import re
from typing import List, Optional

import requests
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def data_lake_file_to_ref_doc(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
    document_parser: DocumentParserResource,
) -> RefDocDocument:
    """Loads the data lake file using the data lake file system, parses the file using the parser, returns the
    parsed document as a RefDocDocument with adding all metadata from the data lake to the RefDocDocument.
    Also extracts and saves any figures to the data lake.
    """
    reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)

    context.log.info(f"Using reader {reader.__class__.__name__} for document of type {data_lake_file.filetype}")

    documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
    document = documents[0]

    ref_doc = RefDocDocument(**document.dict())
    ref_doc.add_metadata_from_data_lake_file(data_lake_file)

    # Process and save figures if operation_id exists
    if (
        "operation_id" in document.extra_info
        and "figure_count" in document.extra_info
        and document.extra_info["figure_count"] > 0
    ):
        document_intelligence_client = DocumentIntelligenceAccess().get_client()
        operation_id = document.extra_info["operation_id"]
        figure_ids = document.extra_info["figure_ids"]

        # Extract and save raw figure data
        saved_figures_paths = save_figures_to_data_lake(
            context, figure_ids, operation_id, document_intelligence_client, data_lake_file
        )

        ref_doc = inject_figures(context, ref_doc, saved_figures_paths)

        # Remove the operation_id from metadata
        if "operation_id" in ref_doc.metadata:
            del ref_doc.metadata["operation_id"]

    return ref_doc


def save_figures_to_data_lake(
    context: OpExecutionContext,
    figure_ids: List[str],
    operation_id: str,
    document_intelligence_client,
    data_lake_file: DataLakeFile,
) -> List[str]:
    """
    Extracts and saves raw figure data to Azure Data Lake using BlobServiceClient.

    Args:
        context: The operation execution context
        figure_ids: List of figure_ids from the document intelligence result
        operation_id: The operation ID for retrieving figure data
        document_intelligence_client: The document intelligence client
        data_lake_file: The source data lake file

    Returns:
        List of paths to the saved figures
    """
    figure_paths = []
    account_url = "https://aihubdevstchedatalake.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

    # TODO check if base_path is what you expect it to be
    base_path = os.path.dirname(data_lake_file.uri)
    doc_id = data_lake_file.id_
    figures_dir = f"{base_path.strip('/')[1:]}/figures/{doc_id}"
    container_name = base_path.strip("/")[0]

    context.log.info(f"Saving {len(figure_ids)} figures to {figures_dir}")

    for idx, figure_id in enumerate(figure_ids):
        try:
            # Get the raw figure data using the specified approach
            response = document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=operation_id,
                figure_id=figure_id,
            )

            # Combine all chunks of the response
            response_bytes = bytes()
            for chunk in response:
                response_bytes += chunk

            # Default extension
            extension = "png"

            blob_path = f"{figures_dir}/figure_{idx + 1}.{extension}"
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
            blob_client.upload_blob(response_bytes)

            figure_paths.append(blob_path)

        except Exception as e:
            context.log.error(f"Failed to save figure {idx + 1}: {str(e)}")
            # Log the full exception for debugging
            context.log.error(f"Exception details: {type(e).__name__}: {str(e)}")

    return figure_paths


def inject_figures(
    context: OpExecutionContext,
    document: RefDocDocument,
    figure_paths: List[str],
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
    updated_content = document.content
    figures_replaced = 0

    # Loop through each figure path
    for i, image_path in enumerate(figure_paths):
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
                # Parse the container and blob path from the figure path
                path_parts = image_path.strip("/").split("/")
                container_name = path_parts[0]
                blob_path = "/".join(path_parts[1:])

                # Download the image
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
                image_data = blob_client.download_blob().readall()

                # Generate description with context
                description = generate_description(
                    context, image_data, figure_index=i, surrounding_text=surrounding_text
                )
                context.log.info(f"Generated contextual description for figure {i+1}")
            except Exception as e:
                context.log.error(f"Error processing image {i+1} for description: {str(e)}")
                description = f"Figure {i+1}"

        # Create markdown image tag with description
        markdown_image = f"![{description}]({image_path})"

        # Replace the figure tag with the markdown image using the exact span positions
        updated_content = updated_content[:start] + markdown_image + updated_content[end:]
        figures_replaced += 1

    # Update the document content
    document.content = updated_content
    context.log.info(
        f"Updated document content with {figures_replaced} markdown image tags with contextual descriptions."
    )

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
        api_key = os.environ.get("OPENAI_API_KEY")

        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Create a robust system prompt
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

        # Prepare the API request
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                    ],
                },
            ],
            "max_tokens": 500,
            "temperature": 0.2,  # Lower temperature for more deterministic, factual outputs
        }

        # Make the API request
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        # Parse the response
        if response.status_code == 200:
            result = response.json()
            description = result["choices"][0]["message"]["content"]

            return description
        else:
            context.log.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return f"Figure {figure_index + 1}"

    except Exception as e:
        context.log.error(f"Failed to generate image description: {str(e)}")
        return f"Figure {figure_index + 1}"
