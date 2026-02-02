from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

from playground.agent.HitlDemoAgent.events.HitlTypeSelectionRequestEvent import HitlTypeSelectionRequestEvent
from playground.agent.HitlDemoAgent.events.HitlTypeSelectionResponseEvent import HitlTypeSelectionResponseEvent


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
