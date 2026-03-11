from swiss_ai_hub.core.events.process import AgentWorkEvent

from playground.agents.AgentB.events.AgentBStopEvent import AgentBStopEvent


class AgentBWork(AgentWorkEvent[AgentBStopEvent]):
    pass
