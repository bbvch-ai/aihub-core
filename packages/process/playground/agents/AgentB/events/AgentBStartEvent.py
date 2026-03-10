from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent


class AgentBStartEvent(StartEvent):
    payload: str
