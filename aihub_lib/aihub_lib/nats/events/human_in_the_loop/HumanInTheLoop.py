from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopConfirmationResponseEvent,
    HumanInTheLoopInputResponseEvent,
    HumanInTheLoopResponseEvent,
)
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


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


class HumanInTheLoopConfirmation:
    """Helper for triggering yes/no confirmation HITL steps within a workflow."""

    request = HumanInTheLoopConfirmationRequestEvent
    response = HumanInTheLoopConfirmationResponseEvent

    @classmethod
    def invoke(cls, question: str) -> HumanInTheLoopConfirmationRequestEvent:
        """Create a request for yes/no confirmation from a human operator."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )


class HumanInTheLoop:
    """
    A helper for triggering human-in-the-loop (HITL) steps within a workflow.

    Use the specific helpers for type-safe interactions:
    - `HumanInTheLoop.input` for free-form text input
    - `HumanInTheLoop.confirmation` for yes/no confirmation

    Or use the base classes directly via `request` and `response` attributes.
    """

    request = HumanInTheLoopRequestEvent
    response = HumanInTheLoopResponseEvent

    # Typed helpers
    input = HumanInTheLoopInput
    confirmation = HumanInTheLoopConfirmation
