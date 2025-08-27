import time
from typing import Annotated, Any, ClassVar

from bson import ObjectId
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopResponseEvent(ControlAndDisplayEvent):
    """
    A response from a human operator after a HITL request.

    ### Why HumanInTheLoopResponseEvent?
    Once a human operator provides an answer to a `HumanInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on human input.
    - Is visible to the UI (since it's also a `DisplayEvent`), allowing transparency and auditing.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's answer or decision.")]
    request_event: Annotated[
        HumanInTheLoopRequestEvent,
        Field(
            description="The original `HumanInTheLoopRequestEvent` that led to this response, providing context "
            "for where and why the workflow paused.",
        ),
    ]

    @classmethod
    def from_raw_data(
        cls,
        raw_event_data: dict[str, Any],
        start_event_name: str,
        start_event_parents: list[str],
        **args,
    ) -> "HumanInTheLoopResponseEvent":
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_parent_event_names": start_event_parents,
            "_event_name": start_event_name,
        }
        return cls.deserialize_event(json_data)
