from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText
from swiss_ai_hub.core.nats.events.process.start.ProcessStartEvent import ProcessStartEvent
from swiss_ai_hub.core.nats.events.work.human.HumanWorkEvent import HumanWorkEvent


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputText | str, Field(description="Input text A")]
