from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.agent_a.events.agent_a_start_event import AgentAStartEvent
from playground.events.agent_a_work import AgentAWork


class AgentAWorkRequest(AgentWorkRequestEvent[AgentAStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentAWork
