from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig


class ImapAgentConfig(AgentConfig):
    """Configuration for the IMAP demonstrator agent — nests the reusable IMAP connection config and the grouped
    draft-email settings (which message to read, which model drafts it, and where the draft lands)."""

    imap: Annotated[
        ImapClientConfig,
        Field(description="IMAP connection used to read the mailbox."),
    ]
    draft: Annotated[
        DraftEmailSettings,
        Field(title="Draft email settings", description="Reply-drafting behaviour, model, and target folder."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            imap=ImapClientConfig.as_form(),
            draft=DraftEmailSettings.as_form(),
        )
