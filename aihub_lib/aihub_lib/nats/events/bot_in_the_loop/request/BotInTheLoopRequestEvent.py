from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class BotInTheLoopRequestEvent(ControlEvent):
    """
    An event asking a human for input, guidance, or approval at a critical juncture in a workflow.

    ### Why HumanInTheLoopRequestEvent?
    In automated workflows, certain decisions may require human validation. This event:
    - Carries a question and a topic indicating where the subsequent response should be sent.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.bitl_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.bitl_request_event.description"
    )

    user: Annotated[
        UserIdentity,
        Field(
            description="The authenticated user who is requesting the human-in-the-loop interaction.",
        ),
    ]
    question: Annotated[str, Field(description="The query or prompt presented to the human operator.")]
    slack_channel_id: Annotated[
        str | None,
        Field(description="The ID of the Slack channel where the request is sent to.", pattern=r"^C[0-9A-Z]+$"),
    ] = None
    teams_channel_id: Annotated[
        str | None,
        Field(description="The ID of the Teams channel where the request is sent to.", pattern=r"^.+$"),
    ] = None
    topic: Annotated[
        PartialAgentTopic | AgentInstanceTopic,
        Field(
            description="A partial or full agent topic specifying the event type and name of the expected response "
            "event, ensuring the correct workflow step resumes once the human replies.",
        ),
    ]
