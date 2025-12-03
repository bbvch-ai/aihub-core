from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent, ProcessStartEvent
from pydantic import Field


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[str, Field(description="Input text A")]
