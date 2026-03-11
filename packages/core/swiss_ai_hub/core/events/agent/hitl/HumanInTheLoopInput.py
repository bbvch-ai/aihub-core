from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)
from swiss_ai_hub.core.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoopInput:
    """Helper for triggering text input HITL steps within a workflow."""

    request = HumanInTheLoopInputRequestEvent
    response = HumanInTheLoopInputResponseEvent

    @classmethod
    def invoke(cls, question: str) -> HumanInTheLoopInputRequestEvent:
        """Create a request for free-form text input from a human operator."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
