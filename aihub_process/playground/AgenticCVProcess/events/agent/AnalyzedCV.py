from aihub_lib.nats.events import BaseEvent, StopEvent, LLMStopEvent
from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[LLMStopEvent]):
    pass
