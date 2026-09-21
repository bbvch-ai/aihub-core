from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.memory.request.store_user_memory_requested_event import (
    StoreUserMemoryRequestedEvent,
)


class MemoryStorageRequestedEvent(ControlEvent):
    """
    Detached delegation request: tells the dispatcher to start an independent `MemoryWriterAgent` run to
    persist user memory, WITHOUT awaiting a response (issue #1179).

    ### Why a dedicated pure control event (not AgentInTheLoop)?
    `AgentInTheLoopRequestEvent` is also a `DisplayEvent`, so it renders a delegation step in the user's chat
    after the answer — the exact symptom #1179 removes — and it opens a response subscription that would route
    a result back into the caller's run stores (deleted at stop). This event is **control-only**: the
    dispatcher publishes the wrapped `start_event` to the writer's subject and nothing is routed back. Because
    it is a plain control event it also lands in the caller's event store when published, so it doubles as the
    stop-gate marker (`check_ready_for_stop`) — the run finalizes as soon as this cheap marker exists, not when
    storage completes.
    """

    start_event: Annotated[
        StoreUserMemoryRequestedEvent,
        Field(description="The start event published to the writer agent to begin its independent run."),
    ]
    target_agent_class: Annotated[str, Field(description="Writer agent class to route the start event to.")]
    target_agent_id: Annotated[str, Field(description="Writer agent id (fixed system id) to route to.")]
