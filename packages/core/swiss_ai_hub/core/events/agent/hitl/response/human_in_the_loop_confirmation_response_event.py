from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event import (
    HumanInTheLoopConfirmationRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInTheLoopConfirmationResponseEvent(HumanInTheLoopResponseEvent[HumanInTheLoopConfirmationRequestEvent]):
    """Response containing yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.description"
    )

    response: Annotated[bool, Field(description="The human operator's confirmation (True for yes, False for no).")]
