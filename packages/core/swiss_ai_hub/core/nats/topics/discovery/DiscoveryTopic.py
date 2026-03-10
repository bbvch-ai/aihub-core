from typing import Self

from swiss_ai_hub.core.nats.topic_managers.TopicManager import TopicManager
from swiss_ai_hub.core.nats.topics.Topic import Topic


class DiscoveryTopic(Topic):
    discovery_topic: str
    request_response: str
    call_id: str

    @property
    def execution_context_id(self) -> str:
        return self.call_id

    @classmethod
    def from_subject(cls, subject: str) -> Self:
        topic_type, discovery_topic, request_response, call_id = subject.split(".")
        assert (
            topic_type == TopicManager.INSTANCE_DISCOVERY_TOPIC or topic_type == TopicManager.CLASS_DISCOVERY_TOPIC
        ), f"Trying to parse a non-discovery topic: {subject}"
        return cls(discovery_topic=discovery_topic, request_response=request_response, call_id=call_id)
