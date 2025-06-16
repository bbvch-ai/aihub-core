from typing import ClassVar, Type

from aihub_lib.nats.events import AgentWorkRequestEvent, AgentWorkEvent
from playground.minimal_processes.agent_only_process.AgentB.events.AgentBStartEvent import AgentBStartEvent
from playground.minimal_processes.agent_only_process.events.AgentBWork import AgentBWork


class AgentBWorkRequest(AgentWorkRequestEvent[AgentBStartEvent]):
    work: ClassVar[Type[AgentWorkEvent]] = AgentBWork

