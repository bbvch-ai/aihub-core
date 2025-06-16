from aihub_lib.nats.events import ProcessStartEvent
from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from playground.minimal_processes.agent_only_process.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentAWork(ProcessStartEvent, AgentWorkEvent[AgentAStopEvent]):
    pass
