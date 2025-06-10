import base64
import logging
import re
from typing import Dict, List, Optional

import httpx
from llama_index.core.base.llms.types import ChatMessage

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.infrastructure.azure.data_lake.DataLakeAccess import DataLakeAccess


logger = logging.getLogger(__name__)


def extract_image_urls_from_nodes(nodes: List[IngestedNode]) -> List[str]:
    """
    Extract image URLs from markdown image patterns in node content.
    
    Args:
        nodes: List of ingested nodes to search for image URLs
        
    Returns:
        List of unique image URLs found in the nodes
    """
    image_urls_found = []
    for node in nodes:
        # [^\]]{10,1000} matches non bracket characters between 10 and 1000 times, [^\s\)]{10,2048} matches non whitespace and non closing parenthesis characters between 10 and 2048 times
        markdown_image_pattern = r'^!\[[^\]]{10,1000}\]\((https?:\/\/[^\s\)]{10,2048})\)$'
        urls = re.findall(markdown_image_pattern, node.content)
        image_urls_found.extend(urls)
    
    return list(set(image_urls_found))


async def fetch_images_from_urls(image_urls: List[str]) -> List[str]:
    """
    Fetch image data from a list of URLs and return as base64 data URLs.
    
    Args:
        image_urls: List of image URLs to fetch
        
    Returns:
        Dictionary mapping original URLs to base64 data URLs for successfully fetched images
    """
    processed_images = []
    
    for image_url in image_urls:
        try:
            if image_url.startswith("https://bbvaihubdatalake.dfs.core.windows.net/"):
                # Azure blob storage URL - use DataLakeAccess
                image_data = await _fetch_image_from_azure_blob(image_url)
            else:
                logger.warning(f"Unsupported image URL format: {image_url}")
                continue

            if image_data:
                processed_images.append(image_data)
                logger.info(f"Successfully processed image: {image_url}")
            else:
                logger.warning(f"Failed to fetch image data from: {image_url}")

        except Exception as e:
            logger.error(f"Error processing image {image_url}: {e}")
            continue

    return processed_images


async def process_images(
    nodes: List[IngestedNode], 
    context_message: ChatMessage
) -> ChatMessage:
    """
    Complete image processing pipeline: extract URLs from nodes, fetch images, and return processed data.
    
    Args:
        nodes: List of ingested nodes to search for image URLs
        context_message: The original context message
        
    Returns:
        Tuple of (context_message, processed_images_dict, image_urls_found)
    """
    image_urls_found = extract_image_urls_from_nodes(nodes)
    
    if not image_urls_found:
        return context_message, {}, []
    
    processed_images = await fetch_images_from_urls(image_urls_found)
    content = []
    content.append(context_message.content)
    for image in processed_images:
        content.append({"type": "image_url", "image_url": {"url": image}})

    context_message = ChatMessage(
        role=context_message.role,
        content=content
    )
    
    return context_message


async def _fetch_image_from_azure_blob(url: str) -> Optional[str]:
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
        
        fs_client = DataLakeAccess().get_fs_client()
        
        full_path = f"{container_name}/{blob_path}"
        
        with fs_client.open(full_path, 'rb') as f:
            image_bytes = f.read()
        
        file_extension = blob_path.lower().split('.')[-1]
        mime_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml'
        }
        mime_type = mime_type_map.get(file_extension, 'image/jpeg')
        
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"
        
    except Exception as e:
        logger.error(f"Error fetching image from Azure blob {url}: {e}")
        return None
