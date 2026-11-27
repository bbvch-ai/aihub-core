from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent


class InTheLoopTimeoutEvent(ControlAndDisplayEvent):
    """
    A human, agent or bot asked by a run did not answer in time.

    Published by NATS at the request's deadline onto the run's own control subject, so a step declaring the timeout
    next to the response takes the fallback path, even when the process that asked has restarted since. Whichever of
    answer and timeout arrives first settles the request; the other one triggers nothing.
    """

    request_event_id: Annotated[str, Field(description="`event_id` of the request that went unanswered.")]
    timeout_seconds: Annotated[float, Field(description="How long the run waited before giving up.")]
