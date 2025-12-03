from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import HumanWorkEvent, ProcessStartEvent


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[str, Field(description="Input text A")]
