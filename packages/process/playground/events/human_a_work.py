from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.process import HumanWorkEvent, ProcessStartEvent
from swiss_ai_hub.core.form import InputText


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputText | str, Field(description="Input text A")]
