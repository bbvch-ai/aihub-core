from swiss_ai_hub.core.nats.events import StopEvent


class AgentAStopEvent(StopEvent):
    payload: str
