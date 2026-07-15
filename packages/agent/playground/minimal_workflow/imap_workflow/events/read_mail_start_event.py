from typing import Annotated, Literal

from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import StartEvent


class ReadMailStartEvent(StartEvent):
    """Programmatic start event for the IMAP demonstrator — non-conversational, like RetrievalAgent's QuestionStartEvent.

    Using a dedicated start event instead of UserMessageEvent keeps the agent out of the chat UI (is_conversational
    stays False): it is configured via its form and triggered programmatically or by another workflow, not chatted with.
    """

    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language for display output.")] = "en"
    user: Annotated[
        UserIdentity | None,
        Field(default=None, description="User the run is executed on behalf of; populated when triggered via the API."),
    ]
