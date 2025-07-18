from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[BaseEvent]):
    cv_name: str
