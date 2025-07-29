from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import StartEvent


class TestStartEvent(StartEvent):
    payload: Annotated[str, Field(description="Test payload for the start event.")]
