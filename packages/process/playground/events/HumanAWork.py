from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import HumanWorkEvent, ProcessStartEvent
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText


class HumanAWork(HumanWorkEvent, ProcessStartEvent):
    payload: Annotated[InputText | str, Field(description="Input text A")]
