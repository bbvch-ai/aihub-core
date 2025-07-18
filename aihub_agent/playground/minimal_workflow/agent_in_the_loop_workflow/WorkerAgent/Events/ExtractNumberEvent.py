from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ExtractNumberEvent(ControlEvent):
    number: Annotated[int, Field(description="The extracted number value from the input")]
