from typing import ClassVar

from swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent import AgentWorkEvent
from swiss_ai_hub.core.events.process.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.events.AgentBWork import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentBWork
