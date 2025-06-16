from aihub_lib.nats.events import StopEvent


class AgentAStopEvent(StopEvent):
    payload: str