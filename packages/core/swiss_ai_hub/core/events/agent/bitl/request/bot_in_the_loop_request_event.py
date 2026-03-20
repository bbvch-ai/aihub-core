from typing import Annotated, ClassVar, Self

from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.form.constraints import Pattern
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic

# Regex patterns for config validation
TEAMS_CHANNEL_ID_PATTERN = r"^[0-9]+:[a-zA-Z0-9_-]+@thread\.(tacv2|skype)$"
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SLACK_CHANNEL_ID_PATTERN = r"^C[0-9A-Z]+$"


class TeamsConfig(Form):
    """Teams channel configuration with form duality support."""

    channel_id: Annotated[
        str | InputText,
        Field(description="The ID of the Teams channel where the request is sent to."),
        Pattern(TEAMS_CHANNEL_ID_PATTERN),
    ]
    tenant_id: Annotated[
        str | InputText,
        Field(description="The ID of the Teams tenant where the channel resides (Azure AD tenant ID)."),
        Pattern(UUID_PATTERN),
    ]
    bot_id: Annotated[
        str | InputText,
        Field(description="The UUID of the Teams bot (will be prefixed with '28:' when used in Bot Framework)."),
        Pattern(UUID_PATTERN),
    ]

    @property
    def bot_framework_id(self) -> str:
        """Get the bot ID in Bot Framework format (28:{UUID})."""
        return f"28:{self.bot_id}"

    @classmethod
    def as_form(cls, condition_if: str | None = None) -> Self:
        """Factory method for form-mode TeamsConfig with optional condition_if."""
        return cls(
            channel_id=InputText(
                label=LocaleString(en="Channel ID", de="Kanal-ID", fr="ID du canal", it="ID del canale"),
                help=LocaleString(
                    en="Teams channel ID (e.g., 19:abc123@thread.tacv2)",
                    de="Teams-Kanal-ID (z.B. 19:abc123@thread.tacv2)",
                    fr="ID du canal Teams (ex: 19:abc123@thread.tacv2)",
                    it="ID del canale Teams (es: 19:abc123@thread.tacv2)",
                ),
                condition_if=condition_if,
            ),
            tenant_id=InputText(
                label=LocaleString(en="Tenant ID", de="Mandanten-ID", fr="ID du tenant", it="ID del tenant"),
                help=LocaleString(
                    en="Azure AD tenant ID (UUID)",
                    de="Azure AD Mandanten-ID (UUID)",
                    fr="ID du tenant Azure AD (UUID)",
                    it="ID del tenant Azure AD (UUID)",
                ),
                condition_if=condition_if,
            ),
            bot_id=InputText(
                label=LocaleString(en="Bot ID", de="Bot-ID", fr="ID du bot", it="ID del bot"),
                help=LocaleString(
                    en="Teams bot UUID",
                    de="Teams-Bot-UUID",
                    fr="UUID du bot Teams",
                    it="UUID del bot Teams",
                ),
                condition_if=condition_if,
            ),
        )


class SlackConfig(Form):
    """Slack channel configuration with form duality support."""

    channel_id: Annotated[
        str | InputText,
        Field(description="The ID of the Slack channel where the request is sent to."),
        Pattern(SLACK_CHANNEL_ID_PATTERN),
    ]
    service_url: Annotated[
        str | InputText,
        Field(
            description="The Bot Framework service URL for Slack (OAuth & Permissions Redirect URL). "
            "Common values: 'https://slack.botframework.com' (global) or 'https://europe.slack.botframework.com' (EU).",
        ),
    ] = "https://slack.botframework.com"

    @classmethod
    def as_form(cls, condition_if: str | None = None) -> Self:
        """Factory method for form-mode SlackConfig with optional condition_if."""
        return cls(
            channel_id=InputText(
                label=LocaleString(en="Channel ID", de="Kanal-ID", fr="ID du canal", it="ID del canale"),
                help=LocaleString(
                    en="Slack channel ID (e.g., C123ABC)",
                    de="Slack-Kanal-ID (z.B. C123ABC)",
                    fr="ID du canal Slack (ex: C123ABC)",
                    it="ID del canale Slack (es: C123ABC)",
                ),
                condition_if=condition_if,
            ),
            service_url=InputText(
                label=LocaleString(en="Service URL", de="Service-URL", fr="URL du service", it="URL del servizio"),
                help=LocaleString(
                    en="Bot Framework service URL (default: https://slack.botframework.com)",
                    de="Bot-Framework-Service-URL (Standard: https://slack.botframework.com)",
                    fr="URL du service Bot Framework (défaut: https://slack.botframework.com)",
                    it="URL del servizio Bot Framework (default: https://slack.botframework.com)",
                ),
                condition_if=condition_if,
            ),
        )


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
