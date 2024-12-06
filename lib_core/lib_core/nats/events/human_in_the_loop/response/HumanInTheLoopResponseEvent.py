from lib.Events import ControlEvent, DisplayEvent
from lib.Events.HumanInTheLoopEvents.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopResponseEvent(ControlEvent, DisplayEvent):
    response: str
    request_event: HumanInTheLoopRequestEvent
