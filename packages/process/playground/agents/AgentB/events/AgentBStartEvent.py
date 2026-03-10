from swiss_ai_hub.core.nats.events import StartEvent


class AgentBStartEvent(StartEvent):
    payload: str
