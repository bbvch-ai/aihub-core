from typing import ClassVar

from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from swiss_ai_hub.core.nats.events.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent

from playground.agents.AgentC.events.AgentCStartEvent import AgentCStartEvent
from playground.events.AgentCWork import AgentCWork


class AgentCWorkRequest(AgentWorkRequestEvent[AgentCStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentCWork
