from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import HumanWorkEvent


class HumanBWork(HumanWorkEvent):
    payload: Annotated[str, Field(description="Input text B")]
