from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event import (
    HumanInTheLoopConfirmationRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_confirmation_response_event import (
    HumanInTheLoopConfirmationResponseEvent,
)
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic


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
