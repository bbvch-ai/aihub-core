from swiss_ai_hub.core.events.process import ProcessWorkEvent

from playground.events.CustomProcessStopEvent import CustomProcessStopEvent


class InitialProcessWorkEvent(ProcessWorkEvent[CustomProcessStopEvent]):
    pass
