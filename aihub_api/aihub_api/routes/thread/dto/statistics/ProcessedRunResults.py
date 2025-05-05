from typing import Annotated, Dict, Set

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentIdentifier import AgentIdentifier
from aihub_api.routes.thread.dto.statistics.IntermediateDisplayStats import IntermediateDisplayStats


class ProcessedRunResults(BaseModel):
    """Holds the results after processing raw aggregated run data."""

    display_aggregates: Annotated[
        Dict[str, IntermediateDisplayStats],
        Field(default_factory=dict, description="Aggregated statistics for each display, keyed by display ID"),
    ]
    participating_agent_ids: Annotated[
        Set[AgentIdentifier],
        Field(default_factory=set, description="Set of agent identifiers that participated in the thread"),
    ]
