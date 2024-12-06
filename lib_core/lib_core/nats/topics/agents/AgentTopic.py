from typing import Optional

from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class AgentTopic(PartialAgentTopic):
    agent_class: str
    agent_id: str
    run_id: str
    thread_id: str
    display_id: str
    event_type: str
    event_name: str

    def __str__(self) -> str:
        return f"agent.{self.agent_class}.{self.agent_id}.{self.thread_id}.{self.display_id}.{self.run_id}.{self.event_type}.{self.event_name}"

    @classmethod
    def from_subject(cls, subject: str) -> 'AgentTopic':
        _, agent_class, agent_id, thread_id, display_id, run_id, event_type, event_name = subject.split(".")
        return cls(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            event_type=event_type,
            event_name=event_name,
        )

    @classmethod
    def from_partial_topic(
        cls,
        partial_topic: PartialAgentTopic,
        agent_class: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        display_id: Optional[str] = None,
        event_type: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> 'AgentTopic':
        return cls(
            agent_class=partial_topic.agent_class or agent_class,
            agent_id=partial_topic.agent_id or agent_id,
            run_id=partial_topic.run_id or run_id,
            thread_id=partial_topic.thread_id or thread_id,
            display_id=partial_topic.display_id or display_id,
            event_type=partial_topic.event_type or event_type,
            event_name=partial_topic.event_name or event_name,
        )
