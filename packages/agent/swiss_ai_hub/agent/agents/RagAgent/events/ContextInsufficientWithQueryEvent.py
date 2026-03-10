from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events.guard.ContextInsufficientRejectEvent import ContextInsufficientRejectEvent


class ContextInsufficientWithQueryEvent(ContextInsufficientRejectEvent):
    new_query: Annotated[
        str | None, Field(description="The new query to retrieve better context, if max_hops has not been exceeded.")
    ] = None
