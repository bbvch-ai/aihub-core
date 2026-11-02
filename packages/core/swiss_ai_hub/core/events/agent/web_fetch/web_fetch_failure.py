from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure_reason import WebFetchFailureReason


class WebFetchFailure(BaseModel):
    """A linked page the agent could not read, with the reason the answer reports to the user."""

    url: Annotated[str, Field(description="The URL as the user sent it.")]
    reason: Annotated[WebFetchFailureReason, Field(description="Why the page could not be read.")]
