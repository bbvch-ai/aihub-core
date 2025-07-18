from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.form.InputTextElement import InputTextElement
from pydantic import Field


class RejectCV(HumanWorkEvent):
    reason: Annotated[InputTextElement | str, Field(description="Gives a reason why this CV is rejected")]
