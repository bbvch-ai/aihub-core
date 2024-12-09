from typing import Dict, Any

from lib_core.nats.events.control.ControlEvent import ControlEvent
from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class SemanticEvent(ControlEvent, DisplayEvent):
    def to_semantic_convention(self) -> Dict[str, Any]:
        raise NotImplementedError
