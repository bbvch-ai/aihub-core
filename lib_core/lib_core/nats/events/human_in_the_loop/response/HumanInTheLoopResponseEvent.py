from lib_core.nats.events.display.DisplayEvent import DisplayEvent
from lib_core.nats.events.control.ControlEvent import ControlEvent
from lib_core.nats.events.human_in_the_loop import HumanInTheLoopRequestEvent


class HumanInTheLoopResponseEvent(ControlEvent, DisplayEvent):
    response: str
    request_event: HumanInTheLoopRequestEvent
