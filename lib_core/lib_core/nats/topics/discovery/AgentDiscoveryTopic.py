from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topics import DiscoveryTopic


class AgentDiscoveryTopic(DiscoveryTopic):
    agent_class: str
    agent_id: str

    @classmethod
    def from_subject(cls, subject: str) -> "DiscoveryTopic":
        topic_type, discovery_topic, agent_class, agent_id, request_response, call_id = subject.split(".")
        assert topic_type == TopicManager.DISCOVERY_TOPIC, f"Trying to parse a non-discovery topic: {subject}"
        assert discovery_topic == TopicManager.AGENT_TOPIC, f"Trying to parse a non-agent discovery topic: {subject}"
        return cls(
            discovery_topic=discovery_topic,
            agent_class=agent_class,
            agent_id=agent_id,
            request_response=request_response,
            call_id=call_id,
        )

