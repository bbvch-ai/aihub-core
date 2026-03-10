from swiss_ai_hub.core.nats.events import StartEvent


class AgentAStartEvent(StartEvent):
    payload: str
