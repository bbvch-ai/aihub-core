from typing import Annotated, Self

from pydantic import Field

from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.AgentClassTopic import AgentClassTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class AgentInstanceTopic(AgentClassTopic):
    """
    Represents a fully-defined agent event topic. Unlike PartialAgentTopic, all fields are expected
    to be present. This includes identifiers for agent_class, agent_id, and the event itself.

    ### Why This Class Exists

    In a hierarchical event topic model, PartialAgentTopic might not have all details filled out.
    AgentTopic guarantees that every piece of the event route—from agent class to event ID—is known.
    This makes AgentTopic ideal for scenarios where the full path is required, such as final message
    routing or logging a complete event identifier.

    ### Example:
    If an event subject is something like:
    "agent.myclass.myid.thread123.displayA.run45.display_event.some_event.789"
    then this AgentTopic can represent it, providing quick field-level access and serialization.
    """

    agent_id: Annotated[str, Field(description="Unique identifier for the specific agent instance.")]

    def __str__(self) -> str:
        """Returns the full subject string for this agent topic."""
        return (
            f"{AgentTopicManager.AGENT_TOPIC}."
            f"{self.agent_class}."
            f"{self.agent_id}."
            f"{self.thread_id}."
            f"{self.display_id}."
            f"{self.run_id}."
            f"{self.event_type}."
            f"{self.event_name}."
            f"{self.event_id}"
        )

    @classmethod
    def from_partial_topic(
        cls,
        partial_topic: PartialAgentTopic,
        agent_class: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        event_type: str | None = None,
        event_name: str | None = None,
        event_id: str | None = None,
    ) -> Self:
        """
        Converts a PartialAgentTopic into a fully-defined AgentTopic, filling in any missing fields
        from the provided optional parameters.

        This allows turning a partial topic (where some fields may be None) into a complete one,
        ensuring that all attributes have values.
        """
        return cls(
            agent_class=partial_topic.agent_class or agent_class,
            agent_id=partial_topic.agent_id or agent_id,
            run_id=partial_topic.run_id or run_id,
            thread_id=partial_topic.thread_id or thread_id,
            display_id=partial_topic.display_id or display_id,
            event_type=partial_topic.event_type or event_type,
            event_name=partial_topic.event_name or event_name,
            event_id=partial_topic.event_id or event_id,
        )

    @classmethod
    def from_agent_class_topic(
        cls,
        agent_class_topic: AgentClassTopic,
        agent_id: Annotated[str, Field(description="Unique identifier for the specific agent instance.")],
    ) -> Self:
        """
        Constructs an AgentInstanceTopic from an AgentClassTopic and a specific agent_id.
        """
        return cls(
            agent_class=agent_class_topic.agent_class,
            agent_id=agent_id,
            thread_id=agent_class_topic.thread_id,
            display_id=agent_class_topic.display_id,
            run_id=agent_class_topic.run_id,
            event_type=agent_class_topic.event_type,
            event_name=agent_class_topic.event_name,
            event_id=agent_class_topic.event_id,
        )
