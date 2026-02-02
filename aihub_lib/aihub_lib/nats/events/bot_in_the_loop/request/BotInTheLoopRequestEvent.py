from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class TeamsConfig(BaseModel):
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the Teams channel where the request is sent to.",
            pattern=r"^[0-9]+:[a-zA-Z0-9_-]+@thread\.(tacv2|skype)$",
        ),
    ]
    tenant_id: Annotated[
        str,
        Field(
            description="The ID of the Teams tenant where the channel resides (Azure AD tenant ID).",
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        ),
    ]
    bot_id: Annotated[
        str,
        Field(
            description="The UUID of the Teams bot (will be prefixed with '28:' when used in Bot Framework).",
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        ),
    ]

    @property
    def bot_framework_id(self) -> str:
        """Get the bot ID in Bot Framework format (28:{UUID})."""
        return f"28:{self.bot_id}"


class SlackConfig(BaseModel):
    channel_id: Annotated[
        str, Field(description="The ID of the Slack channel where the request is sent to.", pattern=r"^C[0-9A-Z]+$")
    ]
    service_url: Annotated[
        str,
        Field(
            description="The Bot Framework service URL for Slack (OAuth & Permissions Redirect URL). "
            "Common values: 'https://slack.botframework.com' (global) or 'https://europe.slack.botframework.com' (EU).",
        ),
    ] = "https://slack.botframework.com"


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
    channel_config: Annotated[
        SlackConfig | TeamsConfig,
        Field(description="Configuration details for sending the request via Slack or Teams."),
    ]
    topic: Annotated[
        PartialAgentTopic | AgentInstanceTopic,
        Field(
            description="A partial or full agent topic specifying the event type and name of the expected response "
            "event, ensuring the correct workflow step resumes once the human replies.",
        ),
    ]
