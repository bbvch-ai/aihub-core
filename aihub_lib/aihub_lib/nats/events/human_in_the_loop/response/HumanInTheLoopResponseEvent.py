import time
from typing import Annotated, Any, ClassVar

from bson import ObjectId
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopChatRequestEvent,
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopRequestEvent,
)


class HumanInTheLoopResponseEvent(ControlAndDisplayEvent):
    """
    Base response from a human operator after a HITL request.

    Use the specific subclasses:
    - `HumanInTheLoopInputResponseEvent` for text input responses
    - `HumanInTheLoopConfirmationResponseEvent` for yes/no confirmation responses
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_response_event.description"
    )

    response: Annotated[str | bool, Field(description="The human operator's response.")]
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


class HumanInTheLoopInputResponseEvent(HumanInTheLoopResponseEvent):
    """Response containing free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's text input.")]
    request_event: Annotated[
        HumanInTheLoopInputRequestEvent,
        Field(description="The original input request event."),
    ]


class HumanInTheLoopConfirmationResponseEvent(HumanInTheLoopResponseEvent):
    """Response containing yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.description"
    )

    response: Annotated[bool, Field(description="The human operator's confirmation (True for yes, False for no).")]
    request_event: Annotated[
        HumanInTheLoopConfirmationRequestEvent,
        Field(description="The original confirmation request event."),
    ]


class HumanInTheLoopChatResponseEvent(HumanInTheLoopResponseEvent):
    """Response containing user's chat message text."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_chat_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_chat_response_event.description"
    )

    response: Annotated[str, Field(description="The user's chat message response.")]
    request_event: Annotated[
        HumanInTheLoopChatRequestEvent,
        Field(description="The original chat request event."),
    ]
