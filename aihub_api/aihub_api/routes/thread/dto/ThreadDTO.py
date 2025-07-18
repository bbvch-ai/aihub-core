import logging
from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.thread.dto.statistics.DisplayStatistics import DisplayStatistics
from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO

logger = logging.getLogger(__name__)


class ThreadDTO(BaseModel):
    """Thread information and statistics for API response."""

    # Basic thread information
    id: Annotated[str, Field(description="The thread ID")]
    name: Annotated[str, Field(description="User given name of thread")]
    users: Annotated[list[MinimalUserDTO], Field(description="List of users in thread")]
    agents: Annotated[list[MinimalAgentDTO], Field(description="List of agents initially associated with thread")]
    created_at: Annotated[str, Field(description="Date at which thread was created (ISO format string)")]

    process_class: Annotated[str | None, Field(description="Class of the process that generated the thread")] = None
    process_id: Annotated[str | None, Field(description="ID of the process that generated the thread")] = None
    process_walkthrough_id: Annotated[
        str | None, Field(description="ID of the walkthrough that generated the thread")
    ] = None

    # Aggregated Event statistics for the whole thread
    num_events: Annotated[int, Field(description="Total number of events in the thread")] = 0
    num_turns: Annotated[int, Field(description="Number of turns (StartEvent count)")] = 0
    has_pending: Annotated[
        bool, Field(description="Thread has more StartEvent than StopEvent+ExceptionEvent overall")
    ] = False
    has_errors: Annotated[bool, Field(description="There are ExceptionEvent in the thread")] = False
    is_hitl: Annotated[bool, Field(description="There are HumanInTheLoopRequest events present")] = False
    open_hitl: Annotated[bool, Field(description="More HumanInTheLoopRequest than Response overall")] = False
    is_bitl: Annotated[bool, Field(description="There are BotInTheLoopRequest events present")] = False
    open_bitl: Annotated[bool, Field(description="More BotInTheLoopRequest than Response overall")] = False
    is_aitl: Annotated[bool, Field(description="There are AgentInTheLoopRequest events present")] = False
    open_aitl: Annotated[bool, Field(description="More AgentInTheLoopRequest than Response overall")] = False

    # Overall Timing fields for the thread
    first_interaction: Annotated[
        str | None, Field(description="Date of oldest event in thread (ISO format string)")
    ] = None
    latest_interaction: Annotated[
        str | None, Field(description="Date of newest event in thread (ISO format string)")
    ] = None
    duration: Annotated[float | None, Field(description="Overall duration of interactions in seconds")] = None

    # Enhanced statistics / Contents
    displays: Annotated[list[DisplayStatistics], Field(description="Displays in this thread, sorted by start time")] = (
        []
    )
    participating_agents: Annotated[
        list[MinimalAgentDTO], Field(description="All unique agents that participated in the thread's events")
    ] = []
    llm_cost: Annotated[float, Field(description="Total LLM cost of the thread")] = 0.0
