from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class TestStopEvent(StopEvent):
    payload: Annotated[str, Field(description="Test payload for the stop event.")]
