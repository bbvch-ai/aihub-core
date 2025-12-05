from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class ExpertInTheLoopRequestEvent(ControlAndDisplayEvent):
    """
    An event asking an expert for input via the built-in GUI.

    This event is part of the Expert-in-the-Loop pattern, which allows the system to pause execution
    and request expert guidance through a web-based GUI interface instead of external messaging
    platforms like Slack or Teams.

    The event is both a ControlEvent (affects workflow) and DisplayEvent (visible in UI),
    allowing experts to see and respond to pending questions directly in the platform.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.eitl_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.eitl_request_event.description"
    )

    user: Annotated[
        UserIdentity,
        Field(
            description="The authenticated user who is requesting expert input.",
        ),
    ]
    question: Annotated[
        str,
        Field(description="The question or prompt presented to the expert."),
    ]
    context: Annotated[
        str | None,
        Field(description="Additional context to help the expert answer the question (e.g., retrieved documents)."),
    ] = None
    expert_group: Annotated[
        str | None,
        Field(description="Optional identifier for the group of experts who should see this question."),
    ] = None
    priority: Annotated[
        Literal["low", "normal", "high", "urgent"],
        Field(description="Priority level of the question."),
    ] = "normal"
    locale: Annotated[
        Literal["de", "en", "fr", "it"],
        Field(description="The language of the question."),
    ] = "en"
    topic: Annotated[
        PartialAgentTopic | AgentInstanceTopic,
        Field(
            description="A partial or full agent topic specifying where the response event should be directed, "
            "ensuring the correct workflow step resumes once the expert replies.",
        ),
    ]
