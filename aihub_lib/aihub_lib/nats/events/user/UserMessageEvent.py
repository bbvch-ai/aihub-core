from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.start.StartEvent import StartEvent
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

    locale: Annotated[
        str,
        Field(
            description="The user’s locale, defaults to a system-wide default locale, "
            "guiding language or regional adaptations.",
        ),
    ] = LocaleHandler.DEFAULT_LOCALE
    user: Annotated[UserIdentity, Field(description="User who sent the message")]
    messages: Annotated[
        list[ChatMessage],
        Field(
            description="A list of chat messages (user and assistant) that provide context, enabling the agent to "
            "understand what the user is asking for and what has been discussed so far.",
        ),
    ] = []
    files: Annotated[
        list[UserUploadedFile] | None,
        Field(
            description="A list of files that the user has uploaded, which can be used to provide "
            "additional context or information for the agent.",
        ),
    ] = None

    @property
    def user_query(self) -> str:
        """
        Extracts the user query text from the chat history, returning the last user message content.
        Note: This only returns text content. Use last_user_message for full message with all blocks.
        """
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        return user_messages[-1].content if user_messages else ""

    @property
    def last_user_message(self) -> ChatMessage:
        """
        Extracts the complete last user message (with all blocks including images/audio) from chat history.
        Use this when passing messages to LLMs to preserve multimodal content.
        """
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        return user_messages[-1] if user_messages else ChatMessage(role=MessageRole.USER, content="")
