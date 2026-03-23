from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.agent_c.events.agent_c_start_event import AgentCStartEvent
from playground.events.agent_c_work import AgentCWork


class AgentCWorkRequest(AgentWorkRequestEvent[AgentCStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentCWork
