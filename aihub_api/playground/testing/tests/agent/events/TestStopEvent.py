from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import StopEvent


class TestStopEvent(StopEvent):
    payload: Annotated[str, Field(description="Test payload for the stop event.")]
