
from aihub_lib.nats.events import StartEvent

from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent


class AskExpertStartEvent(AskExpertEvent, StartEvent):
    pass
