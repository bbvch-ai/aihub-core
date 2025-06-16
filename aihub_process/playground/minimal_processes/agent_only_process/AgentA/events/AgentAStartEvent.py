from aihub_lib.nats.events import StartEvent


class AgentAStartEvent(StartEvent):
    payload: str
