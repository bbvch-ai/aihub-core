from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopChatRequestEvent import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopResponseEvent,
)


class HumanInTheLoopChatResponseEvent(HumanInTheLoopResponseEvent[HumanInTheLoopChatRequestEvent]):
    """Response containing chat-style input from a human operator.

    This response is sent when a user replies to a chat HITL request via
    a normal chat message instead of a popup dialog.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_chat_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_chat_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's chat message.")]
