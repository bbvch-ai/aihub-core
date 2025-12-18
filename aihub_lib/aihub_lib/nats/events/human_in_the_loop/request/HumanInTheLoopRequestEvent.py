from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

# Type discriminator for HITL request events
HitlRequestType = Literal["input", "confirmation", "chat"]


class HumanInTheLoopRequestEvent(ControlAndDisplayEvent):
    """
    Base event asking a human for input, guidance, or approval at a critical juncture in a workflow.

    Use the specific subclasses:
    - `HumanInTheLoopInputRequestEvent` for free-form text input (popup dialog)
    - `HumanInTheLoopConfirmationRequestEvent` for yes/no confirmation (popup dialog)
    - `HumanInTheLoopChatRequestEvent` for chat-style input (appears as regular message)
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_request_event.description"
    )

    question: Annotated[str, Field(description="The query or prompt presented to the human operator.")]
    topic: Annotated[
        PartialAgentTopic | AgentInstanceTopic,
        Field(
            description="A partial or full agent topic specifying the event type and name of the expected response "
            "event, ensuring the correct workflow step resumes once the human replies.",
        ),
    ]
    hitl_type: Annotated[
        HitlRequestType,
        Field(
            description="The type of HITL interaction: 'input' for free-form text, 'confirmation' for yes/no.",
        ),
    ]


class HumanInTheLoopInputRequestEvent(HumanInTheLoopRequestEvent):
    """Request free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_request_event.description"
    )

    hitl_type: Annotated[
        Literal["input"],
        Field(default="input", description="Fixed to 'input' for text input requests."),
    ] = "input"


class HumanInTheLoopConfirmationRequestEvent(HumanInTheLoopRequestEvent):
    """Request yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.description"
    )

    hitl_type: Annotated[
        Literal["confirmation"],
        Field(default="confirmation", description="Fixed to 'confirmation' for yes/no requests."),
    ] = "confirmation"


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
