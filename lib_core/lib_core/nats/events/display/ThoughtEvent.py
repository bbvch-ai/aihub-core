from pydantic import Field

from lib.Events.DisplayEvent.DisplayEvent import DisplayEvent


class ThoughtEvent(DisplayEvent):
    content: str = Field(..., description="The content of the thought")
