from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import StopEvent


class TestStopEvent(StopEvent):
    payload: Annotated[str, Field(description="Test payload for the stop event.")]
