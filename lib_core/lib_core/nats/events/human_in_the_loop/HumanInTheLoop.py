from lib_core.nats.events.human_in_the_loop import HumanInTheLoopRequestEvent, HumanInTheLoopResponseEvent
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoop:
    request = HumanInTheLoopRequestEvent
    response = HumanInTheLoopResponseEvent

    @classmethod
    def invoke(cls, **kwargs):
        return cls.request(
            **kwargs,
            topic=PartialAgentTopic(
                event_type=TopicManager.CONTROL_EVENT,
                event_name=HumanInTheLoopResponseEvent.__name__
            ),
        )
