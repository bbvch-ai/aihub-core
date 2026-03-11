from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent


class ExpertAnswerInsufficientEvent(ControlEvent):
    """Event representing an insufficient answer from the experts"""

    response: Annotated[str, Field(description="Answer given by experts")]
    expert_user_id: Annotated[str, Field(description="User ID of the expert who answered")]
    expert_name: Annotated[str, Field(description="Name of the expert who answered")]
