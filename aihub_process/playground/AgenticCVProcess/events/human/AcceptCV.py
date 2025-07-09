from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import HumanWorkEvent
from aihub_lib.nats.events.work_request.human.form.InputTextElement import InputTextElement


class AcceptCV(HumanWorkEvent):
    reason: Annotated[InputTextElement | str, Field(description="Gives a reason why this CV is accepted")]
