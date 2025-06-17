from typing import ClassVar, Type

from aihub_lib.nats.events import AgentWorkRequestEvent, AgentWorkEvent
from playground.events.AgentBWork import AgentBWork
from playground.agents.AgentB.events.AgentBStartEvent import AgentBStartEvent


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[Type[AgentWorkEvent]] = AgentBWork
