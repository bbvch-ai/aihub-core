from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import WebFetchFailure


class ExtractedUrls(BaseModel):
    """The URLs found in a message, split up front: a malformed or unsupported one is reported without ever
    reaching the browser."""

    urls: Annotated[list[str], Field(description="Well-formed http(s) URLs to fetch, in message order.")] = []
    failures: Annotated[
        list[WebFetchFailure], Field(description="URLs rejected before fetching, with the reason for each.")
    ] = []
