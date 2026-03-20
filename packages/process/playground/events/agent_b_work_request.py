from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.agent_b.events.agent_b_start_event import AgentBStartEvent
from playground.events.agent_b_work import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentBWork
