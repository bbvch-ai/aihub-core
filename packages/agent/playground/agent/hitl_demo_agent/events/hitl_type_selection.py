from swiss_ai_hub.core.events.agent import HumanInTheLoopInput
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from playground.agent.hitl_demo_agent.events.hitl_type_selection_request_event import HitlTypeSelectionRequestEvent
from playground.agent.hitl_demo_agent.events.hitl_type_selection_response_event import HitlTypeSelectionResponseEvent


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
