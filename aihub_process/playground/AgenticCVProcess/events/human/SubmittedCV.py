from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import ProcessStartEvent, HumanWorkEvent
from aihub_lib.nats.events.form import InputTextElement


class SubmittedCV(HumanWorkEvent, ProcessStartEvent):
    # name: str
    # qualifications: list[str]
    name: Annotated[InputTextElement | str, Field(description="Name of the applicant")]
