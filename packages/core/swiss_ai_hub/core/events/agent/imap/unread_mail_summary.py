from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class UnreadMailSummary(BaseModel):
    """Lightweight header summary of one unread message — enough for an agent to decide what to fetch."""

    message_id: Annotated[str, Field(description="IMAP message identifier used to fetch the full message.")]
    sender: Annotated[str, Field(description="Raw From header of the message.")]
    subject: Annotated[str, Field(description="Subject header of the message.")]
    date: Annotated[datetime | None, Field(default=None, description="Date header of the message, if parseable.")]
    flags: Annotated[list[str], Field(default_factory=list, description="IMAP flags set on the message.")]
