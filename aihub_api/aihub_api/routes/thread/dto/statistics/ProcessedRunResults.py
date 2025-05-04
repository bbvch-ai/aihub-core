from typing import Dict, Set

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentIdentifier import AgentIdentifier
from aihub_api.routes.thread.dto.statistics.IntermediateDisplayStats import IntermediateDisplayStats


class ProcessedRunResults(BaseModel):
    """Holds the results after processing raw aggregated run data."""

    display_aggregates: Dict[str, IntermediateDisplayStats] = Field(default_factory=dict)
    participating_agent_ids: Set[AgentIdentifier] = Field(default_factory=set)
