from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent


class AgentBStopEvent(StopEvent):
    payload: str
