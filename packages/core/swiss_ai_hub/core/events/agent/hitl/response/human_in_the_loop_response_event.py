from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


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
    _api_server_fields: ClassVar[frozenset[str]] = BaseEvent._api_server_fields | {"responded_by"}

    response: Annotated[str | bool, Field(description="The human operator's response.")]
    request_event: Annotated[
        THitlRequestEvent,
        Field(
            description="The original `HumanInTheLoopRequestEvent` that led to this response, providing context "
            "for where and why the workflow paused.",
        ),
    ]
    responded_by: Annotated[
        str | None,
        Field(
            description="The id of the user who answered. Set by the server from the authenticated sender, never "
            "taken from the client; none when no user answered.",
        ),
    ] = None
