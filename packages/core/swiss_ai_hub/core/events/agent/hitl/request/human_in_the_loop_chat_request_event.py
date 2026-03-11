from typing import ClassVar, Literal

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInTheLoopChatRequestEvent(HumanInTheLoopRequestEvent):
    """Request chat-style input from a human operator.

    Unlike input/confirmation types that show popup dialogs, chat requests appear
    as regular chat messages. The user responds by typing a normal chat message.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_chat_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_chat_request_event.description"
    )

    hitl_type: Literal["chat"] = "chat"
