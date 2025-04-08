from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent
from aihub_lib.nats.events import StartEvent


class AskExpertStartEvent(AskExpertEvent, StartEvent):
    pass
