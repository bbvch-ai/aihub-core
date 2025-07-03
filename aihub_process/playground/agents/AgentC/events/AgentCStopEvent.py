from aihub_lib.nats.events import StopEvent


class AgentCStopEvent(StopEvent):
    payload: str
