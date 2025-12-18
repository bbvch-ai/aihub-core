from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HitlTypeSelectionRequestEvent(HumanInTheLoopInputRequestEvent):
    """Custom request for HITL type selection."""
    pass


class HitlTypeSelectionResponseEvent(HumanInTheLoopInputResponseEvent):
    """Custom response for HITL type selection."""

    pass


class HitlTypeSelection(HumanInTheLoopInput):
    """Helper for the HITL type selection step."""

    request = HitlTypeSelectionRequestEvent
    response = HitlTypeSelectionResponseEvent

    @classmethod
    def invoke(cls, question: str) -> HitlTypeSelectionRequestEvent:
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
