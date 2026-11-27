from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic


class AgentDelegation(BaseModel):
    """
    Who started a run through `AgentInTheLoop`, carried on the delegated run's start event.

    The delegated run's dispatcher answers the caller from it when the run stops or fails, through JetStream, so the
    answer survives a restart of either side. It also bounds chains of delegations by their depth.
    """

    caller: Annotated[AgentInstanceTopic, Field(description="The delegating run, where the answer is published.")]
    request_event_id: Annotated[str, Field(description="`event_id` of the caller's `AgentInTheLoopRequestEvent`.")]
    depth: Annotated[int, Field(ge=1, description="1 for a run delegated to by a run nobody delegated to, and so on.")]
