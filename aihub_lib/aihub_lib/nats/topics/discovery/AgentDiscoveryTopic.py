from pydantic import Field

from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics import DiscoveryTopic


class AgentDiscoveryTopic(DiscoveryTopic):
    """
    Specialization of DiscoveryTopic for agent-specific discovery subjects, including agent_class and agent_id.

    ### Why AgentDiscoveryTopic?
    While DiscoveryTopic covers generic discovery patterns, some discovery calls specifically target an
    agent or a class of agents. AgentDiscoveryTopic provides a structured view of these more granular
    queries or responses, allowing the system to quickly identify which agent (by class and ID) is involved.
    """

    agent_class: str = Field(..., description="Agent class targeted by the discovery.")
    agent_id: str = Field(..., description="Specific agent instance targeted by the discovery.")

    @classmethod
    def from_subject(cls, subject: str) -> "AgentDiscoveryTopic":
        """
        Use this when dealing with agent-specific discovery subjects to extract agent_class and agent_id.
        """
        (
            topic_type,
            discovery_topic,
            agent_class,
            agent_id,
            request_response,
            call_id,
        ) = subject.split(".")
        assert topic_type == TopicManager.DISCOVERY_TOPIC, f"Unexpected topic type: {subject}"
        assert discovery_topic == TopicManager.AGENT_TOPIC, f"Not an agent discovery topic: {subject}"

        return cls(
            discovery_topic=discovery_topic,
            agent_class=agent_class,
            agent_id=agent_id,
            request_response=request_response,
            call_id=call_id,
        )
