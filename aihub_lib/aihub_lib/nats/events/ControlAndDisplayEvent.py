from .control.ControlEvent import ControlEvent
from .display.DisplayEvent import DisplayEvent

class ControlAndDisplayEvent(ControlEvent, DisplayEvent):
    pass