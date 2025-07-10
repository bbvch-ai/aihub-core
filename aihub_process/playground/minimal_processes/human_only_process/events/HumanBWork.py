from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.work_request.human.form.InputTextElement import InputTextElement


class HumanBWork(HumanWorkEvent):
    input_text_b: Annotated[InputTextElement | str, Field(description="Input text B")]