from pydantic import Field

from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class ThoughtEvent(DisplayEvent):
    """
    An event representing the system or agent's internal reasoning process, often displayed as
    a "thought" or debug info stream. These "thoughts" provide insight into how the agent arrives
    at decisions, though they don't influence control flow (since it's a DisplayEvent).

    ### Why ThoughtEvent?
    While `ControlEvent` affects workflow logic, `ThoughtEvent` provides transparency,
    revealing the reasoning paths taken by the agent. Useful for debugging, auditing, or
    explaining the agent’s behavior to end-users (e.g., "chain-of-thought" explanations).
    """

    content: str = Field(..., description="The textual representation of the agent’s internal reasoning at a particular point in time.")
