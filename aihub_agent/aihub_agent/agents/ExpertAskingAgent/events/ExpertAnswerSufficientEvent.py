from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import ControlEvent


class ExpertAnswerSufficientEvent(ControlEvent):
    """Event representing a sufficient answer from the experts"""
    response: Annotated[str, Field(..., description="Answer given by experts")]
    expert_name: Annotated[str, Field(..., description="Name of the expert who answered")]
