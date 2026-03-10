from typing import ClassVar

from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from swiss_ai_hub.core.nats.events.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.AgentAWork import AgentAWork


class AgentAWorkRequest(AgentWorkRequestEvent[AgentAStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentAWork
