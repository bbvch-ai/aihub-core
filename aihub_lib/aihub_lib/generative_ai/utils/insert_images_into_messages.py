import re
import urllib.parse
from typing import List

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.infrastructure.azure.data_lake.DataLakeAccess import DataLakeAccess

# [^\]]{10,5000} matches non bracket characters between 10 and 5000 times, [^\s\)]{10,1000} matches non whitespace and non closing parenthesis characters between 10 and 1000 times
MARKDOWN_IMAGE_PATTERN = r"^!\[[^\]]{10,5000}\]\((https?:\/\/[^\s\)]{10,1000})\)$"


def extract_image_urls_from_nodes(nodes: List[IngestedNode]) -> List[str]:
    image_urls_found = []
    for node in nodes:
        urls = re.findall(MARKDOWN_IMAGE_PATTERN, node.content)
        image_urls_found.extend(urls)

    return list(set(image_urls_found))


async def fetch_images_from_urls(urls: List[str]) -> List[ImageBlock]:
    fs_client = DataLakeAccess().get_fs_client()

    images = []
    for url in urls:
        _, _, _, _, raw_blob_path = url.split("/", 4)
        blob_path = urllib.parse.unquote(raw_blob_path)

        with fs_client.open(blob_path, "rb") as f:
            image_bytes = f.read()

        images.append(ImageBlock(image=image_bytes))

    return images


async def insert_images_into_messages(nodes: List[IngestedNode], messages: List[ChatMessage]) -> List[ChatMessage]:
    """Extract URLs from nodes, fetch images, and insert into messages."""
    image_urls_found = extract_image_urls_from_nodes(nodes)
    if not image_urls_found:
        return messages

    user_message = messages[-1]
    images = await fetch_images_from_urls(image_urls_found)
    content = [TextBlock(text=user_message.content)] + images
    user_message_with_images = ChatMessage(role=user_message.role, content=content)

    messages[-1] = user_message_with_images

    return messages
