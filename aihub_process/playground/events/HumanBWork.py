from typing import Annotated

from aihub_lib.nats.events import HumanWorkEvent
from pydantic import Field


class HumanBWork(HumanWorkEvent):
    payload: Annotated[str, Field(description="Input text B")]
