from typing import Annotated

from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class KeepSourcesEvent(ControlEvent):
    """
    Emitted when user confirms they want to keep current sources after topic change.

    This occurs when the topic change router detected a potential topic change,
    but the user responded that they want to continue with the current sources.
    """

    current_sources: Annotated[
        list[KnowledgeSource],
        Field(description="The current knowledge sources to keep using"),
    ]

    reasoning: Annotated[
        str,
        Field(description="Reasoning from user's response interpretation"),
    ]
