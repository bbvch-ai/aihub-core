from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.memory.request.store_user_memory_requested_event import (
    StoreUserMemoryRequestedEvent,
)
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MemoryStorageRequestedEvent(ControlAndDisplayEvent):
    """
    Detached delegation request: tells the dispatcher to start an independent `MemoryWriterAgent` run to
    persist user memory, WITHOUT awaiting a response (issue #1179).

    ### Why a dedicated event (not AgentInTheLoop)?
    `AgentInTheLoopRequestEvent` renders a delegation step in the user's chat after the answer — the exact
    symptom #1179 removes — and it opens a response subscription that would route a result back into the
    caller's run stores (deleted at stop). Here the dispatcher publishes the wrapped `start_event` to the
    writer's subject and nothing is routed back. It is displayed like every protocol event, so the event
    history shows the delegation; chat clients show no more than a passing status. Its control copy lands in the
    caller's event store when published, so it doubles as the stop-gate marker (`check_ready_for_stop`) — the
    run finalizes as soon as this cheap marker exists, not when storage completes.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.memory_storage_requested_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.memory_storage_requested_event.description"
    )

    start_event: Annotated[
        StoreUserMemoryRequestedEvent,
        Field(description="The start event published to the writer agent to begin its independent run."),
    ]
    target_agent_class: Annotated[str, Field(description="Writer agent class to route the start event to.")]
    target_agent_id: Annotated[str, Field(description="Writer agent id (fixed system id) to route to.")]
