from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.imap import ImapClientConfig


class ImapAgentConfig(AgentConfig):
    """Configuration for the IMAP demonstrator agent — nests the reusable IMAP connection config."""

    imap: Annotated[
        ImapClientConfig,
        Field(description="IMAP connection used to read the mailbox."),
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
        )
