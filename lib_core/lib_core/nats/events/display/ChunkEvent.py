from pydantic import Field

from lib.Events.DisplayEvent.DisplayEvent import DisplayEvent


class ChunkEvent(DisplayEvent):
    content: str = Field(..., description="The content of the chunk")
