from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInTheLoopInputResponseEvent(HumanInTheLoopResponseEvent[HumanInTheLoopInputRequestEvent]):
    """Response containing free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's text input.")]
