from aihub_lib.nats.events import LLMEvent, StopEvent


class LLMStopEvent(LLMEvent, StopEvent):
    pass
