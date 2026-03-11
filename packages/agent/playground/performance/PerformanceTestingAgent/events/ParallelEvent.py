from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent


class ParallelEvent(ControlEvent):
    index: int
    payload: str
