from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent
from swiss_ai_hub.core.events.process import AgentWorkRequestEvent

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.AgentAWork import AgentAWork


class AgentAWorkRequest(AgentWorkRequestEvent[AgentAStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentAWork
