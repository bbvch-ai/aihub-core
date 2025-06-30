from typing import ClassVar, Type

from aihub_lib.nats.events import AgentWorkRequestEvent, AgentWorkEvent
from playground.agents.AgentC.events.AgentCStartEvent import AgentCStartEvent
from playground.events.AgentCWork import AgentCWork


class AgentCWorkRequest(AgentWorkRequestEvent[AgentCStartEvent]):
    work: ClassVar[Type[AgentWorkEvent]] = AgentCWork
