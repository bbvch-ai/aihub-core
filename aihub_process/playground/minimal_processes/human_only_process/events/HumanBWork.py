from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.form.InputTextElement import InputTextElement
from pydantic import Field


class HumanBWork(HumanWorkEvent):
    input_text_b: Annotated[InputTextElement | str, Field(description="Input text B")]
