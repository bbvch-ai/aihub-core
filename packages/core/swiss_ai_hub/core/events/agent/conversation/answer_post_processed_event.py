from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class AnswerPostProcessedEvent(ControlEvent):
    """
    Marker that a post-answer hook has finished with the answer, whether or not it did anything.

    The stop step waits for one per installed hook, so the run finalizes only after every hook — memory
    storage today — has had its turn, without the stop step knowing which hooks exist or are enabled.
    """

    source: Annotated[str, Field(description="The hook that reported, e.g. `user_memory`.")]
