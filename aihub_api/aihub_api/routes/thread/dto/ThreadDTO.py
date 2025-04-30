from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentDTO import MinimalAgentDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class BaseEventStatistics(BaseModel):
    """Base class for event statistics with common fields."""

    n_events: Annotated[int, Field(description="Total number of events")] = 0
    has_errors: Annotated[bool, Field(description="Has error events")] = False
    has_pending: Annotated[bool, Field(description="Has pending events (more start than stop events)")] = False

    # HITL fields
    is_hitl: Annotated[bool, Field(description="Has HITL events")] = False
    open_hitl: Annotated[bool, Field(description="Has open HITL requests")] = False

    # BITL fields
    is_bitl: Annotated[bool, Field(description="Has BITL events")] = False
    open_bitl: Annotated[bool, Field(description="Has open BITL requests")] = False

    # AITL fields
    is_aitl: Annotated[bool, Field(description="Has AITL events")] = False
    open_aitl: Annotated[bool, Field(description="Has open AITL requests")] = False

    # Timing fields
    started_at: Annotated[Optional[datetime], Field(description="Start time")] = None
    ended_at: Annotated[Optional[datetime], Field(description="End time")] = None
    latency: Annotated[Optional[float], Field(description="Latency in seconds")] = None


class EventStatistics(BaseEventStatistics):
    """Detailed event statistics with event counts and timing information."""

    start_events: Annotated[int, Field(description="Number of start events")] = 0
    stop_events: Annotated[int, Field(description="Number of stop events")] = 0
    exception_events: Annotated[int, Field(description="Number of exception events")] = 0
    hitl_request_events: Annotated[int, Field(description="Number of HITL request events")] = 0
    hitl_response_events: Annotated[int, Field(description="Number of HITL response events")] = 0
    bitl_request_events: Annotated[int, Field(description="Number of BITL request events")] = 0
    bitl_response_events: Annotated[int, Field(description="Number of BITL response events")] = 0
    aitl_request_events: Annotated[int, Field(description="Number of AITL request events")] = 0
    aitl_response_events: Annotated[int, Field(description="Number of AITL response events")] = 0
    first_event_time: Annotated[Optional[datetime], Field(description="Time of the first event")] = None
    latest_event_time: Annotated[Optional[datetime], Field(description="Time of the latest event")] = None


class IdentifiableEventStatistics(BaseEventStatistics):
    """Base class for identifiable event statistics objects like runs and displays."""

    started_at: Annotated[Optional[str], Field(description="Start time")] = None
    ended_at: Annotated[Optional[str], Field(description="End time")] = None


class RunStatistics(IdentifiableEventStatistics):
    """Statistics for a single run."""

    run_id: Annotated[str, Field(description="The run ID")]
    agent: Annotated[MinimalAgentDTO, Field(description="The agent that ran the run")]


class DisplayStatistics(IdentifiableEventStatistics):
    """Statistics for a display, including its runs."""

    display_id: Annotated[str, Field(description="The display ID")]
    runs: Annotated[List[RunStatistics], Field(description="Runs in this display")] = []


class ThreadDTO(BaseModel):
    """Thread information and statistics."""

    # Basic thread information
    id: Annotated[str, Field(description="The thread ID")]
    name: Annotated[str, Field(description="User given name of thread")]
    users: Annotated[List[UserDTO], Field(description="List of users in thread")]
    agents: Annotated[List[MinimalAgentDTO], Field(description="List of agents in thread")]
    created_at: Annotated[str, Field(description="Date at which thread was created")]

    # Event statistics
    num_events: Annotated[int, Field(description="Total number of events in the thread")] = 0
    num_turns: Annotated[int, Field(description="Number of turns (StartEvent count)")] = 0
    has_pending: Annotated[bool, Field(description="Thread has more StartEvent than StopEvent")] = False
    has_errors: Annotated[bool, Field(description="There are ExceptionEvent in the thread")] = False

    # HITL/BITL/AITL fields
    is_hitl: Annotated[bool, Field(description="There are HumanInTheLoopRequest events present")] = False
    open_hitl: Annotated[
        bool, Field(description="There are more HumanInTheLoopRequest than HumanInTheLoopResponse")
    ] = False
    is_bitl: Annotated[bool, Field(description="There are BotInTheLoopRequest events present")] = False
    open_bitl: Annotated[bool, Field(description="There are more BotInTheLoopRequest than BotInTheLoopResponse")] = (
        False
    )
    is_aitl: Annotated[bool, Field(description="There are AgentInTheLoopRequest events present")] = False
    open_aitl: Annotated[
        bool, Field(description="There are more AgentInTheLoopRequest than AgentInTheLoopResponse")
    ] = False

    # Timing fields
    first_interaction: Annotated[Optional[str], Field(description="Date of oldest event in thread")] = None
    latest_interaction: Annotated[Optional[str], Field(description="Date of newest event in thread")] = None
    latency: Annotated[Optional[float], Field(description="Average latency of the thread in seconds")] = None

    # Enhanced statistics
    displays: Annotated[List[DisplayStatistics], Field(description="Displays in this thread")] = []
    participating_agents: Annotated[
        List[MinimalAgentDTO], Field(description="Agents that participated in the thread")
    ] = []
    llm_cost: Annotated[float, Field(description="Total LLM cost of the thread")] = 0.0
