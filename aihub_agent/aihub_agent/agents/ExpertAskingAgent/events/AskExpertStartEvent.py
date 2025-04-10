from aihub_lib.nats.events import StartEvent

from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent


class AskExpertStartEvent(AskExpertEvent, StartEvent):
    """Event representing a request to a group of experts for assistance by a user."""

    pass
