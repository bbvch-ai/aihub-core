"""HITL events for namespace approval confirmation."""

from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopConfirmationRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopConfirmationResponseEvent import (
    HumanInTheLoopConfirmationResponseEvent,
)
from swiss_ai_hub.core.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.PartialAgentTopic import PartialAgentTopic


class NamespaceApprovalRequestEvent(HumanInTheLoopConfirmationRequestEvent):
    """Request for user to approve proposed namespace selection."""

    pass


class NamespaceApprovalResponseEvent(HumanInTheLoopConfirmationResponseEvent):
    """Response containing user's approval or rejection of proposed namespaces."""

    pass


class NamespaceApprovalHitl:
    """Helper for triggering namespace approval HITL steps."""

    request = NamespaceApprovalRequestEvent
    response = NamespaceApprovalResponseEvent

    @classmethod
    def invoke(cls, question: str) -> NamespaceApprovalRequestEvent:
        """Create a request for namespace approval from the user."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
