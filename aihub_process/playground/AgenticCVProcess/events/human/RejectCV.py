from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.form.elements.InputText import InputText
from pydantic import Field


class RejectCV(HumanWorkEvent):
    reason: Annotated[InputText | str, Field(description="Gives a reason why this CV is rejected")]
