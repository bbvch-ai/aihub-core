from swiss_ai_hub.core.events.agent import ControlEvent


class ParallelEvent(ControlEvent):
    index: int
    payload: str
