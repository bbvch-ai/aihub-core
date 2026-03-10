from swiss_ai_hub.core.nats.events import ControlEvent


class SimpleEventA(ControlEvent):
    payload: str
