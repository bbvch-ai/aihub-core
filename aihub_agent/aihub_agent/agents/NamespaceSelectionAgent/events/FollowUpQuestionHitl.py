"""HITL events for follow-up questions during namespace determination."""

from typing import Annotated

from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
)
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from pydantic import Field


class FollowUpQuestionRequestEvent(HumanInTheLoopInputRequestEvent):
    """Request for a follow-up question to clarify namespace selection.

    Carries available_namespaces so they can be retrieved from request_event
    when processing the response.
    """

    available_namespaces: Annotated[
        dict[str, list[str]],
        Field(
            default_factory=dict,
            description="Map of bucket names to their available namespace names.",
        ),
    ]


class FollowUpQuestionResponseEvent(HumanInTheLoopInputResponseEvent):
    """Response containing user's answer to a follow-up question."""

    request_event: Annotated[
        FollowUpQuestionRequestEvent,
        Field(description="The original FollowUpQuestionRequestEvent that led to this response."),
    ]


class FollowUpQuestionHitl:
    """Helper for triggering follow-up question HITL steps within namespace determination."""

    request = FollowUpQuestionRequestEvent
    response = FollowUpQuestionResponseEvent

    @classmethod
    def invoke(cls, question: str, available_namespaces: dict[str, list[str]]) -> FollowUpQuestionRequestEvent:
        """Create a request for a follow-up question from the user."""
        return cls.request(
            question=question,
            available_namespaces=available_namespaces,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
