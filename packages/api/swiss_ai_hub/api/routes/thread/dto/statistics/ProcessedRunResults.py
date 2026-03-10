from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.agent.dto.AgentIdentifier import AgentIdentifier
from swiss_ai_hub.api.routes.thread.dto.statistics.IntermediateDisplayStats import IntermediateDisplayStats


class ProcessedRunResults(BaseModel):
    """Holds the results after processing raw aggregated run data."""

    display_aggregates: Annotated[
        dict[str, IntermediateDisplayStats],
        Field(description="Aggregated statistics for each display, keyed by display ID"),
    ] = {}
    participating_agent_ids: Annotated[
        set[AgentIdentifier],
        Field(description="Set of agent identifiers that participated in the thread"),
    ] = set()
