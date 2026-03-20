from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent


class RouteOptions(DisplayEvent):
    name: Annotated[str, Field(..., description="For UI purpose only")]
    description: Annotated[str, Field(..., description="For UI purpose only")]
    instructions: Annotated[str, Field(..., description="Instructions for LLM when to route here")]

    event: Annotated[ControlEvent, Field(..., description="Possible event to route to")]

    @classmethod
    def for_event(cls, event: ControlEvent, instructions: str):
        return cls(
            name=event.event_name,
            description=event.__class__.__doc__ or "",
            instructions=instructions,
            event=event,
        )
