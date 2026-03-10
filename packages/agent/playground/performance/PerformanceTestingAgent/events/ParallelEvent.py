from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


class ParallelEvent(ControlEvent):
    index: int
    payload: str
