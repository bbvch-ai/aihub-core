from pydantic import Field

from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class ChunkEvent(DisplayEvent):
    content: str = Field(..., description="The content of the chunk")
