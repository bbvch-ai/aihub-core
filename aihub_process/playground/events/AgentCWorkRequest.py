from typing import ClassVar

from aihub_lib.nats.events import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.AgentC.events.AgentCStartEvent import AgentCStartEvent
from playground.events.AgentCWork import AgentCWork


class AgentCWorkRequest(AgentWorkRequestEvent[AgentCStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentCWork
