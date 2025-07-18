from typing import ClassVar

from aihub_lib.nats.events import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.events.AgentBWork import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentBWork
