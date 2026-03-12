from swiss_ai_hub.core.events.process import ProcessWorkEvent

from playground.events.custom_process_stop_event import CustomProcessStopEvent


class InitialProcessWorkEvent(ProcessWorkEvent[CustomProcessStopEvent]):
    pass
