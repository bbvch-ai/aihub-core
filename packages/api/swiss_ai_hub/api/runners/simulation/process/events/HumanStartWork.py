from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.process.start.ProcessStartEvent import ProcessStartEvent
from swiss_ai_hub.core.events.process.work.human.HumanWorkEvent import HumanWorkEvent
from swiss_ai_hub.core.form.elements.InputText import InputText


class HumanStartEvent(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputText | str, Field(description="Input text A")]
