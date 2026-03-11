from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent import BotInTheLoopRequestEvent
from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class BotInTheLoopResponderInfo(BaseModel):
    """
    Information about a user who responded to a BITL request (Slack/Teams).
    """

    user_id: Annotated[str, Field(description="The Slack user ID.")]
    user_name: Annotated[str, Field(description="The Slack user name.")]
    additional_info: Annotated[dict | None, Field(description="Additional Slack-specific user information.")] = None
    aad_object_id: Annotated[str | None, Field(description="The Azure Active Directory object ID.")] = None


class BotInTheLoopResponseEvent(ControlEvent):
    """
    A response from a bot operator after a HITL request.

    ### Why BotInTheLoopResponseEvent?
    Once a bot operator provides an answer to a `BotInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on bot input.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.bitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.bitl_response_event.description"
    )

    response: Annotated[str, Field(description="The bot operator's answer or decision.")]
    request_event: Annotated[
        BotInTheLoopRequestEvent,
        Field(
            description="The original `BotInTheLoopRequestEvent` that led to this response, providing context "
            "for where and why the workflow paused.",
        ),
    ]
    responder: Annotated[
        BotInTheLoopResponderInfo,
        Field(
            description="Information about the user who responded to the request, "
            "enabling tracking of who provided the input.",
        ),
    ]
