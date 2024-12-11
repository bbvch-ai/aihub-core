from typing import Dict, List, Any, Optional

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.nats.events.control.ControlEvent import ControlEvent
from lib_core.nats.events.control.start.content.AssistantChatMessage import (
    AssistantChatMessage,
)
from lib_core.nats.events.control.start.content.UserChatMessage import UserChatMessage


class StartEvent(ControlEvent):
    locale: Optional[str] = Field(LocaleHandler.DEFAULT_LOCALE, description="Locale of the user")
    messages: List[ChatMessage | UserChatMessage | AssistantChatMessage] = Field(
        description="Chat history leading to this run", default_factory=list
    )

    def to_context_dict(self) -> Dict[str, Any]:
        non_private = {k: v for k, v in self.model_dump().items() if not k.startswith("_")}
        del non_private["event_id"]
        del non_private["created_at"]
        return non_private
