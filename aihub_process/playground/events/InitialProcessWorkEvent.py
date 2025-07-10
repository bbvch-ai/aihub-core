from aihub_lib.nats.events.work.process.ProcessWorkEvent import ProcessWorkEvent

from playground.events.CustomProcessStopEvent import CustomProcessStopEvent


class InitialProcessWorkEvent(ProcessWorkEvent[CustomProcessStopEvent]):
    pass
