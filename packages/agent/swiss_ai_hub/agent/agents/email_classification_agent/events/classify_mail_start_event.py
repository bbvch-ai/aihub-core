from typing import Annotated, Literal

from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import StartEvent


class ClassifyMailStartEvent(StartEvent):
    """Programmatic start event for a classification run.

    A dedicated start event rather than UserMessageEvent keeps the agent out of the chat UI (is_conversational stays
    False): it is configured via its form and triggered programmatically or by a scheduler, not chatted with.
    """

    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language for display output.")] = "en"
    user: Annotated[
        UserIdentity | None,
        Field(default=None, description="User the run is executed on behalf of; populated when triggered via the API."),
    ]
