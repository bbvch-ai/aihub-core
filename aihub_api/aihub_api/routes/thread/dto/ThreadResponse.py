from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class ThreadResponse(BaseModel):
    id: Annotated[str, Field(description="The thread ID")]
    name: Annotated[str, Field(description="User given name of thread")]
    users: Annotated[List[UserDTO], Field(description="List of users in thread")]
    agents: Annotated[List[AgentDTO], Field(description="List of agents in thread")]
    created_at: Annotated[str, Field(description="Date at which thread was created")]

    # Event statistics
    num_events: Annotated[int, Field(description="Total number of events in the thread")] = 0
    num_turns: Annotated[int, Field(description="Number of turns (StartEvent count)")] = 0
    has_pending: Annotated[bool, Field(description="Thread has more StartEvent than StopEvent")] = False
    has_errors: Annotated[bool, Field(description="There are ExceptionEvent in the thread")] = False
    is_hitl: Annotated[bool, Field(description="There are HumanInTheLoopRequest events present")] = False
    open_hitl: Annotated[bool, Field(description="There are more HumanInTheLoopRequest than HumanInTheLoopResponse")] = False
    is_bitl: Annotated[bool, Field(description="There are BotInTheLoopRequest events present")] = False
    open_bitl: Annotated[bool, Field(description="There are more BotInTheLoopRequest than BotInTheLoopResponse")] = False
    is_aitl: Annotated[bool, Field(description="There are AgentInTheLoopRequest events present")] = False
    open_aitl: Annotated[bool, Field(description="There are more AgentInTheLoopRequest than AgentInTheLoopResponse")] = False
    first_interaction: Annotated[Optional[str], Field(description="Date of oldest event in thread")] = None
    latest_interaction: Annotated[Optional[str], Field(description="Date of newest event in thread")] = None
