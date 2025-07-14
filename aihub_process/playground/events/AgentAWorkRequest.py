from typing import ClassVar

from aihub_lib.nats.events import AgentWorkEvent, AgentWorkRequestEvent

from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.events.AgentAWork import AgentAWork


class AgentAWorkRequest(AgentWorkRequestEvent[AgentAStartEvent]):
    work: ClassVar[type[AgentWorkEvent]] = AgentAWork
