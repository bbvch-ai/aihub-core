from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import StartEvent


class TestStartEvent(StartEvent):
    payload: Annotated[str, Field(description="Test payload for the start event.")]
