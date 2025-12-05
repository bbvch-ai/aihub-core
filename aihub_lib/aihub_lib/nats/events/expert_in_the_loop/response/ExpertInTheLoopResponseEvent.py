from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.expert_in_the_loop.request.ExpertInTheLoopRequestEvent import ExpertInTheLoopRequestEvent


class ExpertInTheLoopResponderInfo(BaseModel):
    """
    Information about the expert who responded to the question via the GUI.
    """

    user_id: Annotated[str, Field(description="The unique identifier of the expert user.")]
    user_name: Annotated[str | None, Field(description="The display name of the expert.")] = None
    email: Annotated[str | None, Field(description="The email address of the expert.")] = None
    expert_group: Annotated[str | None, Field(description="The expert group this user belongs to.")] = None


class ExpertInTheLoopResponseEvent(ControlEvent):
    """
    A response from an expert after an Expert-in-the-Loop request via the GUI.

    This event is part of the Expert-in-the-Loop pattern, which allows experts to provide
    answers through a web-based GUI interface. Once an expert provides an answer, this event:
    - Influences the workflow (as a ControlEvent), resuming execution with the expert's input.
    - Contains the original request for context continuity.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.eitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.eitl_response_event.description"
    )

    response: Annotated[str, Field(description="The expert's answer to the question.")]
    request_event: Annotated[
        ExpertInTheLoopRequestEvent,
        Field(
            description="The original ExpertInTheLoopRequestEvent that led to this response, "
            "providing context for where and why the workflow paused.",
        ),
    ]
    responder: Annotated[
        ExpertInTheLoopResponderInfo | None,
        Field(
            description="Information about the expert who responded, " "enabling tracking of who provided the input.",
        ),
    ] = None
