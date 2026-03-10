from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics.Topic import Topic


class PartialAgentTopic(Topic):
    """
    Represents a partially qualified agent event topic, where some fields may be unspecified.
    Wildcards (represented by "*") in the subject translate into None values here.

    ### Why PartialAgentTopic?
    Sometimes you deal with generic subscriptions to broad categories of events - like all display events
    or all events from a particular agent class - without knowing the exact agent_id, thread_id, or event_id.
    PartialAgentTopic captures this scenario, making it explicit which parts of the topic are defined
    and which remain open (None).

    ### Use Cases
    - **Generic Monitoring:** You might subscribe to `agent.myclass.*.*.*.*.display_event.*.*` to monitor
      all display events for a given agent class, regardless of the specific agent instance or thread.
      The resulting PartialAgentTopic shows which filters have been fixed and which are open.
    - **Routing Decisions:** If a system receives a message on a wildcard topic, it can inspect this
      PartialAgentTopic to decide dynamically which handler to invoke based on known fields, leaving
      unknowns as flexible conditions.
    """

    agent_class: Annotated[str | None, Field(description="Agent class or None if unspecified.")] = None
    agent_id: Annotated[str | None, Field(description="Agent ID or None if unspecified.")] = None
    run_id: Annotated[str | None, Field(description="Run ID or None if unspecified.")] = None
    thread_id: Annotated[str | None, Field(description="Thread ID or None if unspecified.")] = None
    display_id: Annotated[str | None, Field(description="Display ID or None if unspecified.")] = None
    event_type: Annotated[str | None, Field(description="Event type or None if unspecified.")] = None
    event_name: Annotated[str | None, Field(description="Event name or None if unspecified.")] = None
    event_id: Annotated[str | None, Field(description="Event ID or None if unspecified.")] = None

    @property
    def execution_context_id(self) -> str:
        return self.run_id

    @classmethod
    def from_subject(cls, subject: str) -> Self:
        """
        Constructs a PartialAgentTopic from a subject string that may contain wildcards.

        Use this when you have a subject and need a structured representation - knowing that some parts
        of the topic might be generalized (wildcards) rather than fully specified. This is common in
        subscription scenarios where you are not targeting a single event, but a category of events.
        """
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
        assert topic_type == AgentTopicManager.AGENT_TOPIC, f"Unexpected topic type in subject: {subject}"

        def none_if_wildcard(value: str) -> str | None:
            return value if value != "*" else None

        return cls(
            agent_class=none_if_wildcard(agent_class),
            agent_id=none_if_wildcard(agent_id),
            thread_id=none_if_wildcard(thread_id),
            display_id=none_if_wildcard(display_id),
            run_id=none_if_wildcard(run_id),
            event_type=none_if_wildcard(event_type),
            event_name=none_if_wildcard(event_name),
            event_id=none_if_wildcard(event_id),
        )

    def to_subject(self):
        return (
            f"{AgentTopicManager.AGENT_TOPIC}."
            f"{self.agent_class or '*'}."
            f"{self.agent_id or '*'}."
            f"{self.thread_id or '*'}."
            f"{self.display_id or '*'}."
            f"{self.run_id or '*'}."
            f"{self.event_type or '*'}."
            f"{self.event_name or '*'}."
            f"{self.event_id or '*'}"
        )
