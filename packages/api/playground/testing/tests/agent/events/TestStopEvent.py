from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import StopEvent


class TestStopEvent(StopEvent):
    payload: Annotated[str, Field(description="Test payload for the stop event.")]
