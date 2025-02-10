from typing import Any, Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.control.start.content.AssistantChatMessage import AssistantChatMessage
from aihub_lib.nats.events.control.start.content.UserChatMessage import UserChatMessage


class StartEvent(ControlEvent):
    """
    An event signaling the start of a new run within a thread, providing initial context such as
    user messages, assistant responses, and locale settings.

    ### Why StartEvent?
    Workflows often begin with a trigger event containing the initial state or prompts necessary
    to begin processing. The `StartEvent` sets the stage for an agent run by including:
    - **Locale**: Determines language-specific behavior or formatting rules.
    - **Chat History**: A series of messages (user and assistant) that lead up to the run, allowing
      the agent to understand the current conversation state and continuity.

    By extending `ControlEvent`, `StartEvent` influences workflow steps—only `ControlEvent` types
    drive the flow. Other event types may provide data or UI updates but do not start or control runs.
    """

    locale: Optional[str] = Field(
        LocaleHandler.DEFAULT_LOCALE,
        description="The user’s locale, defaults to a system-wide default locale, guiding language or regional adaptations.",
    )
    messages: List[ChatMessage | UserChatMessage | AssistantChatMessage] = Field(
        description="A list of chat messages (user and assistant) that provide context, enabling the agent to understand what the user is asking for and what has been discussed so far.",
        default_factory=list,
    )

    def to_context_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary suitable for context injection, excluding internal event fields like
        event_id and created_at. This helps workflows pass only essential context to downstream steps.
        """
        non_private = {k: v for k, v in self.model_dump().items() if not k.startswith("_")}
        # Remove internal fields not needed by downstream steps
        del non_private["event_id"]
        del non_private["created_at"]
        return non_private

    @property
    def user_query(self) -> str:
        """
        Extracts the user query from the chat history, returning the last user message.
        """
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        return user_messages[-1].content if user_messages else ""
