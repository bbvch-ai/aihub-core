from typing import List, Dict
from pydantic import Field
from llama_index.core.base.llms.types import ChatMessage
from aihub_lib.nats.events import ControlEvent


class ProcessedImagesEvent(ControlEvent):
    """
    Event containing the processed images extracted from retrieved nodes along with the original context.
    This event is generated after extracting and fetching images from markdown image nodes.
    """

    context_message_with_images: ChatMessage = Field(
        ..., description="The original context message including the images from the nodes."
    )
