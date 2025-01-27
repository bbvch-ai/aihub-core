from aihub_lib.nats.events import LLMEvent, StopEvent


class LamaIndexLLMStopEvent(LLMEvent, StopEvent):
    pass
