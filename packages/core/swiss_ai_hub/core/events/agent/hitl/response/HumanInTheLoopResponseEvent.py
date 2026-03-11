import time
from typing import Annotated, Any, ClassVar, Self

from bson import ObjectId
from pydantic import Field

from swiss_ai_hub.core.events.agent.ControlAndDisplayEvent import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class HumanInTheLoopResponseEvent[THitlRequestEvent: HumanInTheLoopRequestEvent](ControlAndDisplayEvent):
    """
    Base response from a human operator after a HITL request.

    Use the specific subclasses:
    - `HumanInTheLoopInputResponseEvent` for text input responses (popup dialog)
    - `HumanInTheLoopConfirmationResponseEvent` for yes/no confirmation responses (popup dialog)
    - `HumanInTheLoopChatResponseEvent` for chat-style responses (regular message)
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_response_event.description"
    )

    response: Annotated[str | bool, Field(description="The human operator's response.")]
    request_event: Annotated[
        THitlRequestEvent,
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
    ) -> Self:
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_parent_event_names": start_event_parents,
            "_event_name": start_event_name,
        }
        return cls.deserialize_event(json_data)
