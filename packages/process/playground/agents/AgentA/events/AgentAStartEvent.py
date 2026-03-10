from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent


class AgentAStartEvent(StartEvent):
    payload: str
