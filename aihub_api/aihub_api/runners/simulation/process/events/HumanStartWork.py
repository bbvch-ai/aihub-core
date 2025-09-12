from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent, ProcessStartEvent
from aihub_lib.nats.events.form.InputTextElement import InputTextElement
from pydantic import Field


class HumanStartEvent(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputTextElement | str, Field(description="Input text A")]
