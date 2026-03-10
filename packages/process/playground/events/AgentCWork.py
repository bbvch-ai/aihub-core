from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent

from playground.agents.AgentC.events.AgentCStopEvent import AgentCStopEvent


class AgentCWork(AgentWorkEvent[AgentCStopEvent]):
    pass
