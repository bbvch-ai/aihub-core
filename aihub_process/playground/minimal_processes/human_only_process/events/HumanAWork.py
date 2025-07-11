from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent, ProcessStartEvent
from aihub_lib.nats.events.form.InputTextElement import InputTextElement
from pydantic import Field


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    input_text_a: Annotated[InputTextElement | str, Field(description="Input text A")]
