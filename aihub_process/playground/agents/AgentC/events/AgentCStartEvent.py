from aihub_lib.nats.events import StartEvent


class AgentCStartEvent(StartEvent):
    payload: str
