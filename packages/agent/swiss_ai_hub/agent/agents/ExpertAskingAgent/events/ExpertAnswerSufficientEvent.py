from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import ControlEvent


class ExpertAnswerSufficientEvent(ControlEvent):
    """Event representing a sufficient answer from the experts"""

    response: Annotated[str, Field(description="Answer given by experts")]
    expert_user_id: Annotated[str, Field(description="User ID of the expert who answered")]
    expert_name: Annotated[str, Field(description="Name of the expert who answered")]
