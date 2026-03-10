from swiss_ai_hub.core.nats.events.human_in_the_loop.request import HumanInTheLoopConfirmationRequestEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop.response import HumanInTheLoopConfirmationResponseEvent
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


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
