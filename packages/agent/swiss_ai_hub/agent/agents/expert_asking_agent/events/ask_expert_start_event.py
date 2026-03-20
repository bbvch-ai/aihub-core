from swiss_ai_hub.core.events.agent import StartEvent

from swiss_ai_hub.agent.agents.expert_asking_agent.events.ask_expert_event import AskExpertEvent


class AskExpertStartEvent(AskExpertEvent, StartEvent):
    """Event representing a request to a group of experts for assistance by a user."""

    pass
