from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent, ProcessStartEvent
from aihub_lib.nats.events.form.elements.InputText import InputText
from pydantic import Field


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputText | str, Field(description="Input text A")]
