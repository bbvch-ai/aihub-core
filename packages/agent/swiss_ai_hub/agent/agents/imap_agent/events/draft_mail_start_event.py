from typing import Annotated, Literal

from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import StartEvent


class DraftMailStartEvent(StartEvent):
    """Programmatic start event for the independent drafting capability.

    Triggers the batch drafter, which reads not-yet-drafted messages from the configured source folder and drafts a
    reply for each. Separate from ReadMailStartEvent so drafting can be scheduled and run independently of the
    read/move chain.
    """

    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language for display output.")] = "en"
    user: Annotated[
        UserIdentity | None,
        Field(default=None, description="User the run is executed on behalf of; populated when triggered via the API."),
    ]
