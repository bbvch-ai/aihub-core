from lib_core.nats.events.control.start import StartEvent
from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class UserMessageEvent(DisplayEvent, StartEvent):
    pass
