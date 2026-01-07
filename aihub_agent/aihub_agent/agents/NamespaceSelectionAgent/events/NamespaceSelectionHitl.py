from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInputRequestEvent, HumanInTheLoopInputResponseEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class NamespaceSelectionRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class NamespaceSelectionResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class NamespaceSelectionHitl:
    request = NamespaceSelectionRequestEvent
    response = NamespaceSelectionResponseEvent

    @classmethod
    def invoke(cls, question: str) -> NamespaceSelectionRequestEvent:
        """Create a request for namespace selection from a human operator."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
