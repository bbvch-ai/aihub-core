from swiss_ai_hub.core.nats.events import StopEvent


class AgentBStopEvent(StopEvent):
    payload: str
