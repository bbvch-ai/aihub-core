from aihub_lib.nats.events import StopEvent


class AgentBStopEvent(StopEvent):
    payload: str
