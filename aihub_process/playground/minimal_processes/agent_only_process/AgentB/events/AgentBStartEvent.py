from aihub_lib.nats.events import StartEvent


class AgentBStartEvent(StartEvent):
    payload: str
