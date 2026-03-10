from swiss_ai_hub.core.nats.events.process.start.ProcessStartEvent import ProcessStartEvent
from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent

from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentAWork(ProcessStartEvent, AgentWorkEvent[AgentAStopEvent]):
    pass
