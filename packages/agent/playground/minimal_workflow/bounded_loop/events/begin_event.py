from swiss_ai_hub.core.events.agent import ControlEvent


class BeginEvent(ControlEvent):
    count: int
