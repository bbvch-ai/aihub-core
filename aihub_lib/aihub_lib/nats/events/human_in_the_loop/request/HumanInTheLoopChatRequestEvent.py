from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopChatRequestEvent(HumanInTheLoopRequestEvent):
    """Request chat-style input from a human operator.

    Unlike input/confirmation types that show popup dialogs, chat requests appear
    as regular chat messages. The user responds by typing a normal chat message.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_chat_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_chat_request_event.description"
    )

    hitl_type: Annotated[
        Literal["chat"],
        Field(default="chat", description="Fixed to 'chat' for chat-style requests."),
    ] = "chat"
