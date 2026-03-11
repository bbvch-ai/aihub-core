from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent

from swiss_ai_hub.agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent


class AskExpertStartEvent(AskExpertEvent, StartEvent):
    """Event representing a request to a group of experts for assistance by a user."""

    pass
