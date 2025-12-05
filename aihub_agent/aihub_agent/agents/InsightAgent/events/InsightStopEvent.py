from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class InsightStopEvent(StopEvent):
    """Event representing the conclusion of the InsightAgent's processing."""

    insight_stored: Annotated[bool, Field(description="Whether the insight was successfully stored")] = True
    insight_id: Annotated[str | None, Field(description="The ID of the stored insight")] = None
