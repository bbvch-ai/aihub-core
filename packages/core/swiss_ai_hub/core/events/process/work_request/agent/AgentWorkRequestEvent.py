from typing import Annotated, TypeVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.events.process.work_request.WorkRequestEvent import WorkRequestEvent

TEvent = TypeVar("TEvent", bound=StartEvent)


class AgentWorkRequestEvent[TEvent: StartEvent](WorkRequestEvent):
    """
    Requests an agent to do some work to bring the process one step further. To delegate the work to an agent,
    the agent class and agent id must be specified, as well as the start_event.
    However, the agent_class and agent_id will be added automatically by the process dispatcher.
    """

    agent_class: Annotated[
        str | None,
        Field(
            description="Class of agent to which work shall be delegated. "
            "Automatically injected by the process dispatcher."
        ),
    ] = None
    agent_id: Annotated[
        str | None,
        Field(
            description="ID of agent to which work shall be delegated.Automatically injected by the process dispatcher."
        ),
    ] = None
    start_event: Annotated[TEvent, Field(description="Start event that shall be sent to the agent")]
