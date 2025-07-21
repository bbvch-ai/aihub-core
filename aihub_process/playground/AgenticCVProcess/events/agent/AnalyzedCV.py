from aihub_lib.nats.events import BaseEvent, StopEvent
from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[StopEvent]):
    cv_name: str
