from typing import Annotated

from aihub_lib.nats.events import StartEvent
from pydantic import Field


class TestStartEvent(StartEvent):
    payload: Annotated[str, Field(description="Test payload for the start event.")]
