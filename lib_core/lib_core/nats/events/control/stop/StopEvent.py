from lib_core.nats.events.display.DisplayEvent import DisplayEvent
from lib_core.nats.events.control.ControlEvent import ControlEvent


class StopEvent(ControlEvent, DisplayEvent):
    pass
