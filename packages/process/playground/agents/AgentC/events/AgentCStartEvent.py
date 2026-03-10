from swiss_ai_hub.core.nats.events import StartEvent


class AgentCStartEvent(StartEvent):
    payload: str
