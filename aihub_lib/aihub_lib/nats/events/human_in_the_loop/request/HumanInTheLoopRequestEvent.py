from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

# Type discriminator for HITL request events
HitlRequestType = Literal["input", "confirmation", "chat"]


class HumanInTheLoopRequestEvent[THitlRequestType: HitlRequestType](ControlAndDisplayEvent):
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
        THitlRequestType,
        Field(
            description="The type of HITL interaction: 'input' for free-form text, 'confirmation' for yes/no.",
        ),
    ]
