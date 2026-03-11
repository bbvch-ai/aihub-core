from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent
from swiss_ai_hub.core.events.process import AgentWorkRequestEvent

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.events.AgentBWork import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentBWork
