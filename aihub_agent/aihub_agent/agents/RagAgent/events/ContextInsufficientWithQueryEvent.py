from typing import Annotated

from aihub_lib.nats.events.guard.ContextInsufficientRejectEvent import ContextInsufficientRejectEvent
from pydantic import Field


class ContextInsufficientWithQueryEvent(ContextInsufficientRejectEvent):
    new_query: Annotated[
        str | None, Field(description="The new query to retrieve better context, if max_hops has not been exceeded.")
    ] = None
