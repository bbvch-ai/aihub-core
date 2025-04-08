from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class AskExpertEvent(ControlEvent):
    question_to_expert: Annotated[str, Field(..., description="The question to ask the expert")]
