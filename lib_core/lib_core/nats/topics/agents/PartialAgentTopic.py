from typing import Optional

from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topics.Topic import Topic


class PartialAgentTopic(Topic):
    agent_class: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    thread_id: Optional[str] = None
    display_id: Optional[str] = None
    event_type: Optional[str] = None
    event_name: Optional[str] = None
    event_id: Optional[str] = None

    @classmethod
    def from_subject(cls, subject: str) -> "AgentTopic":
        (
            topic_type,
            agent_class,
            agent_id,
            thread_id,
            display_id,
            run_id,
            event_type,
            event_name,
            event_id,
        ) = subject.split(".")
        assert topic_type == TopicManager.AGENT_TOPIC, f"Trying to parse a non-agent topic: {subject}"
        return cls(
            agent_class=agent_class if agent_class != "*" else None,
            agent_id=agent_id if agent_id != "*" else None,
            thread_id=thread_id if thread_id != "*" else None,
            display_id=display_id if display_id != "*" else None,
            run_id=run_id if run_id != "*" else None,
            event_type=event_type if event_type != "*" else None,
            event_name=event_name if event_name != "*" else None,
            event_id=event_id if event_id != "*" else None,
        )