from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.form.InputTextElement import InputTextElement


class HumanAWork(HumanWorkEvent):
    input_text_a: Annotated[InputTextElement | str, Field(description="Input text A")]