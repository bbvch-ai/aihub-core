from pydantic import Field

from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class ChunkEvent(DisplayEvent):
    model_name: str = Field(..., description="The name of the model")
    content: str = Field(..., description="The content of the chunk")
