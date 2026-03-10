from swiss_ai_hub.core.nats.events import StopEvent


class AgentCStopEvent(StopEvent):
    payload: str
