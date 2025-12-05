from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HitlOption(BaseModel):
    """A predefined response option for human-in-the-loop requests."""

    key: Annotated[str, Field(description="Language-independent identifier for the option (e.g., 'yes', 'no').")]
    label: Annotated[str, Field(description="Localized display label shown to the user.")]


class HumanInTheLoopRequestEvent(ControlAndDisplayEvent):
    """
    An event asking a human for input, guidance, or approval at a critical juncture in a workflow.

    ### Why HumanInTheLoopRequestEvent?
    In automated workflows, certain decisions may require human validation. This event:
    - Is a `DisplayEvent`, so it can appear in user interfaces.
    - Carries a question and a topic indicating where the subsequent response should be sent.
    - Optionally provides predefined options (e.g., Yes/No) for quick selection instead of free-form input.
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
    options: Annotated[
        list[HitlOption] | None,
        Field(
            default=None,
            description="Optional list of predefined response options with key-label pairs. "
            "The key is language-independent (used in response matching), the label is displayed to the user. "
            "When provided, the UI should render these as clickable buttons instead of a text input.",
        ),
    ] = None
