import logging
import re
import urllib.parse
from typing import List, Optional

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.infrastructure.azure.data_lake.DataLakeAccess import DataLakeAccess

logger = logging.getLogger(__name__)


def extract_image_urls_from_nodes(nodes: List[IngestedNode]) -> List[str]:
    """
    Extract image URLs from markdown image patterns in node content.
    """
    image_urls_found = []
    for node in nodes:
        # [^\]]{10,1000} matches non bracket characters between 10 and 1000 times, [^\s\)]{10,2048} matches non whitespace and non closing parenthesis characters between 10 and 2048 times
        markdown_image_pattern = r"^!\[[^\]]{10,1000}\]\((https?:\/\/[^\s\)]{10,2048})\)$"
        urls = re.findall(markdown_image_pattern, node.content)
        image_urls_found.extend(urls)

    return list(set(image_urls_found))


async def fetch_images_from_urls(image_urls: List[str]) -> List[ImageBlock]:
    """
    Fetch image data from a list of URLs and return as base64 data URLs.
    """
    processed_images = []

    for image_url in image_urls:
        try:
            if image_url.startswith("https://bbvaihubdatalake.dfs.core.windows.net/"):
                image_data = await _fetch_image_from_azure_blob(image_url)
            else:
                logger.warning(f"Unsupported image URL format: {image_url}")
                continue

            if image_data:
                processed_images.append(ImageBlock(image=image_data))
                logger.info(f"Successfully processed image: {image_url}")
            else:
                logger.warning(f"Failed to fetch image data from: {image_url}")

        except Exception as e:
            logger.error(f"Error processing image {image_url}: {e}")
            continue

    return processed_images


async def insert_images_into_messages(nodes: List[IngestedNode], messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Complete image processing pipeline: extract URLs from nodes, fetch images, and return processed data.
    """
    image_urls_found = extract_image_urls_from_nodes(nodes)
    if not image_urls_found:
        return messages

    user_message = messages[-1]
    processed_images = await fetch_images_from_urls(image_urls_found)
    content = [TextBlock(text=user_message.content)] + processed_images
    user_message_with_images = ChatMessage(role=user_message.role, content=content)

    messages[-1] = user_message_with_images

    return messages


async def _fetch_image_from_azure_blob(url: str) -> Optional[bytes]:
    """
    Fetch image from Azure blob storage and return as base64 data URL.

    Args:
        url: Azure blob storage URL

    Returns:
        Base64 data URL string or None if fetching failed
    """
    try:
        path_parts = url.replace("https://bbvaihubdatalake.dfs.core.windows.net/", "").split("/", 1)
        if len(path_parts) != 2:
            logger.error(f"Invalid Azure blob URL format: {url}")
            return None

        container_name, blob_path = path_parts
        blob_path = blob_path.replace("%2F", "/")[11:]

        fs_client = DataLakeAccess().get_fs_client()

        full_path = f"{container_name}/{blob_path}"
        full_path = urllib.parse.unquote(full_path)

        with fs_client.open(full_path, "rb") as f:
            image_bytes = f.read()

        return image_bytes

    except Exception as e:
        logger.error(f"Error fetching image from Azure blob {url}: {e}")
        return None
