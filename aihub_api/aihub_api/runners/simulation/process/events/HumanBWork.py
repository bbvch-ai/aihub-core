from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.form.elements.InputText import InputText
from pydantic import Field


class HumanBWork(HumanWorkEvent):
    payload: Annotated[InputText | str, Field(description="Input text B")]
