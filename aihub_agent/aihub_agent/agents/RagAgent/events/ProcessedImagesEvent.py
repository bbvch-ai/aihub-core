from typing import List, Optional

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ProcessedImagesEvent(ControlEvent):
    """
    Event containing the processed images extracted from retrieved nodes along with the original context.
    This event is generated after extracting and fetching images from markdown image nodes.
    """

    images: Optional[List[str]] = Field(
        None, description="A list of uft-8 encoded bytes representing the processed images."
    )
