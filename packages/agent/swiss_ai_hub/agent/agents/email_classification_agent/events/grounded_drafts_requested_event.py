from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent


class GroundedDraftsRequestedEvent(ControlEvent):
    """Marks that the delegations for this run's grounded drafts have been fired, and how many of each kind are due.

    Emitted only when at least one message was actually delegated, and it is what makes `collect_and_draft_step`
    reachable. That step waits on delegated answers, so with none due it could never fire — which is why a run with
    nothing to ground finishes its drafting in `request_grounded_drafts_step` instead and emits no marker at all.

    Carries counts, never bodies. The correlation index that maps each delegation back to its message lives in
    `RunContext`, because it holds mail identifiers for the whole batch and this event is persisted to the audit trail
    and streamed to the frontend — the same reason the drafting chain reads message bodies from the S3 archive rather
    than carrying them on events.
    """

    grounded_count: Annotated[
        int,
        Field(
            description="Delegated RAG runs this step started, and always at least one. The collecting step's join "
            "waits until this many distinct delegations have answered.",
        ),
    ]
    ungrounded_count: Annotated[
        int,
        Field(
            default=0,
            description="Messages due a draft written from the message alone, because their category names no "
            "collection. Drafted by the collecting step, which delegates nothing for them.",
        ),
    ]
    skipped_count: Annotated[
        int,
        Field(
            default=0,
            description="Classified messages that get no draft at all — their category was not opted in, or no "
            "category fitted them.",
        ),
    ]
