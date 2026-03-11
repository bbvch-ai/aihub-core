from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs


class AgentInSpecs(BaseModel):
    """
    Defines the specifications of a piece of work that can be submitted by an agent.
    It is limited to an exact agent by class and id and holds the event specs of the
    agents stop events, as these stop events are translated to work events and submitted
    to the agentic process as inputs.
    """

    agent_class: Annotated[str, Field(description="The class or category of the agent.")]
    agent_id: Annotated[str, Field(description="A unique identifier for the agent instance.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]
