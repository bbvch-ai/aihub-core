from typing import Any, ClassVar, Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from typing_extensions import override

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.start.StartEvent import StartEvent
from aihub_lib.nats.events.user.content import AssistantChatMessage, UserChatMessage
from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile


class UserMessageEvent(StartEvent):
    """
    A start event triggered directly by a user's message, bridging both display and control functionalities.

    ### Why UserMessageEvent?
    While `StartEvent` influences the workflow’s starting point and `DisplayEvent` represents user-facing
    output, a `UserMessageEvent` marks a workflow start initiated by a user’s input. This is common in chat
    interfaces, voice assistants, or interactive dashboards, where a user’s message serves as both:
    - A display event (since it may appear in the UI history).
    - A control event triggering workflow execution from a particular starting step.

    By inheriting from `DisplayEvent` and `StartEvent`:
    - It ensures the event is visible in the user interface, displaying the user’s message.
    - It also sets the workflow in motion, deciding how and where the system responds or which step
      of the workflow to begin with.

    ### Use Case
    In an agent workflow, you might have:
    - **UserMessageEvent**: Initiates the workflow at a certain step due to user input.
    - Another start event from an agent or a system event: Initiates the workflow at a different step
      or with different initial conditions.

    This flexible design allows mixing and matching start events to adapt how and when workflows
    are triggered, depending on the source of the event.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.user_message_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.user_message_event.description"
    )

    locale: str = Field(
        LocaleHandler.DEFAULT_LOCALE,
        description="The user’s locale, defaults to a system-wide default locale, guiding language or regional adaptations.",
    )
    user: AuthenticatedUser = Field(..., description="User who sent the message")
    messages: List[ChatMessage | UserChatMessage | AssistantChatMessage] = Field(
        description="A list of chat messages (user and assistant) that provide context, enabling the agent to understand what the user is asking for and what has been discussed so far.",
        default_factory=list,
    )
    files: Optional[List[UserUploadedFile]] = Field(
        None,
        description="A list of files that the user has uploaded, which can be used to provide additional context or information for the agent.",
    )

    @property
    def user_query(self) -> str:
        """
        Extracts the user query from the chat history, returning the last user message.
        """
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        return user_messages[-1].content if user_messages else ""

    @override
    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Overrides BaseEvent's model_dump to fix the AnyUrl serialization issue.
        """
        data = super().model_dump(**kwargs)

        # Fix the serialized messages
        serialized_messages = []
        for msg in self.messages:
            msg_dict = msg.model_dump()

            # Fix the URLs in blocks
            for block in msg_dict["blocks"]:
                if block["block_type"] in ["audio", "image"] and block.get("url") is not None:
                    block["url"] = str(block["url"])
                    if block.get("path") is not None:
                        block["path"] = str(block["path"])

            serialized_messages.append(msg_dict)

        data["messages"] = serialized_messages

        return data
