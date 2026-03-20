from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs


class ProgramInSpecs(BaseModel):
    """
    Defines a piece of work that can be submitted by a program.
    It holds the information about the exact data that must be submitted as a work event
    in the event specs. It also holds the information about where that work event data
    must be submitted, aka to which route and using which http method.
    The API will then forward the data to the appropriate process.
    """

    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]
