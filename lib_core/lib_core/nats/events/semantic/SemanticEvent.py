from lib_core.nats.events.control.ControlEvent import ControlEvent
from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class SemanticEvent(ControlEvent, DisplayEvent):
    def to_semantic_convention(self) -> dict:
        raise NotImplementedError
