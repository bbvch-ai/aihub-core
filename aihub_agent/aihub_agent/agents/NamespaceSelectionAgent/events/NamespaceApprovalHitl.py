"""HITL events for namespace approval confirmation."""

from typing import Annotated

from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopConfirmationResponseEvent,
)
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from pydantic import Field


class NamespaceApprovalRequestEvent(HumanInTheLoopConfirmationRequestEvent):
    """Request for user to approve proposed namespace selection.

    Carries both proposed_namespaces (what's being proposed) and available_namespaces
    (needed if user rejects and we loop back to determination).
    """

    proposed_namespaces: Annotated[
        dict[str, str],
        Field(
            default_factory=dict,
            description="The proposed namespace selection (bucket_name -> namespace_name).",
        ),
    ]
    available_namespaces: Annotated[
        dict[str, list[str]],
        Field(
            default_factory=dict,
            description="Map of bucket names to their available namespace names.",
        ),
    ]


class NamespaceApprovalResponseEvent(HumanInTheLoopConfirmationResponseEvent):
    """Response containing user's approval or rejection of proposed namespaces."""

    pass


class NamespaceApprovalHitl:
    """Helper for triggering namespace approval HITL steps."""

    request = NamespaceApprovalRequestEvent
    response = NamespaceApprovalResponseEvent

    @classmethod
    def invoke(
        cls,
        question: str,
        proposed_namespaces: dict[str, str],
        available_namespaces: dict[str, list[str]],
    ) -> NamespaceApprovalRequestEvent:
        """Create a request for namespace approval from the user."""
        return cls.request(
            question=question,
            proposed_namespaces=proposed_namespaces,
            available_namespaces=available_namespaces,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
