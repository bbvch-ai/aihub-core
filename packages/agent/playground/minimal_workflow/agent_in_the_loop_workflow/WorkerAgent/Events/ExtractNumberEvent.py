from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


class ExtractNumberEvent(ControlEvent):
    number: Annotated[int, Field(description="The extracted number value from the input")]
