"""HITL events for follow-up questions during namespace determination."""

from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class FollowUpQuestionRequestEvent(HumanInTheLoopInputRequestEvent):
    """Request for a follow-up question to clarify namespace selection."""

    pass


class FollowUpQuestionResponseEvent(HumanInTheLoopInputResponseEvent):
    """Response containing user's answer to a follow-up question."""

    pass


class FollowUpQuestionHitl:
    """Helper for triggering follow-up question HITL steps within namespace determination."""

    request = FollowUpQuestionRequestEvent
    response = FollowUpQuestionResponseEvent

    @classmethod
    def invoke(cls, question: str) -> FollowUpQuestionRequestEvent:
        """Create a request for a follow-up question from the user."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
