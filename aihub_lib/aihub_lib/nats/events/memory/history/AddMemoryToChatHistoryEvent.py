from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class AddMemoryToChatHistoryEvent(ControlAndDisplayEvent):
    """
    A control and display event emitted when an agent extends chat history with retrieved memories.

    ### Why AddMemoryToChatHistoryEvent?
    Large language models are stateless - they don't remember past conversations unless explicitly provided.
    This event signals that the agent has enriched the conversation context with relevant memories from
    previous interactions.

    By prepending memories as a system message, we:
    - Give the LLM access to long-term context beyond the current session
    - Maintain user privacy (memories are scoped to user/organization)
    - Keep the prompt construction process transparent and auditable

    This event serves both workflow control (passing extended context to LLM steps) and user transparency
    (showing what background information influenced the agent's response).
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_memory_to_chat_history_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_memory_to_chat_history_event.description"
    )
    extended_history: Annotated[list[ChatMessage], Field(description="Chat history extended with user memories.")]
