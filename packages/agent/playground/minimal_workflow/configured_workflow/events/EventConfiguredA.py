from swiss_ai_hub.core.nats.events import ControlEvent


class EventConfiguredA(ControlEvent):
    payload: str
