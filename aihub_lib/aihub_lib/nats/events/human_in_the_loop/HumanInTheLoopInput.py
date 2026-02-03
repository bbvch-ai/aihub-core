from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent
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
