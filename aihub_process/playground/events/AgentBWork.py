from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from playground.agents.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentBWork(AgentWorkEvent[AgentBStopEvent]):
    pass
