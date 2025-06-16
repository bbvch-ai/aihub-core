from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from playground.minimal_processes.agent_only_process.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentBWork(AgentWorkEvent[AgentBStopEvent]):
    pass
