from typing import Annotated

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class SelectNewSourcesEvent(ControlEvent):
    """
    Emitted when user confirms they want to select new sources after topic change.

    This occurs when the topic change router detected a topic change,
    and the user confirmed they want to search different knowledge sources.
    """

    reasoning: Annotated[
        str,
        Field(description="Reasoning from user's response interpretation"),
    ]

    user_preference: Annotated[
        str | None,
        Field(description="Any specific source preferences the user mentioned"),
    ] = None
