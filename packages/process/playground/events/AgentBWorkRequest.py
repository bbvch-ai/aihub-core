from typing import ClassVar

from swiss_ai_hub.core.nats.events import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.events.AgentBWork import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentBWork
