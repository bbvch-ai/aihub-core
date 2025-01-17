from typing import Optional

from pydantic import Field

from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics.Topic import Topic


class PartialAgentTopic(Topic):
    """
    Represents a partially qualified agent event topic, where some fields may be unspecified.
    Wildcards (represented by "*") in the subject translate into None values here.

    ### Why PartialAgentTopic?
    Sometimes you deal with generic subscriptions to broad categories of events—like all display events
    or all events from a particular agent class—without knowing the exact agent_id, thread_id, or event_id.
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

    agent_class: Optional[str] = Field(None, description="Agent class or None if unspecified.")
    agent_id: Optional[str] = Field(None, description="Agent ID or None if unspecified.")
    run_id: Optional[str] = Field(None, description="Run ID or None if unspecified.")
    thread_id: Optional[str] = Field(None, description="Thread ID or None if unspecified.")
    display_id: Optional[str] = Field(None, description="Display ID or None if unspecified.")
    event_type: Optional[str] = Field(None, description="Event type or None if unspecified.")
    event_name: Optional[str] = Field(None, description="Event name or None if unspecified.")
    event_id: Optional[str] = Field(None, description="Event ID or None if unspecified.")

    @classmethod
    def from_subject(cls, subject: str) -> "PartialAgentTopic":
        """
        Constructs a PartialAgentTopic from a subject string that may contain wildcards.

        Use this when you have a subject and need a structured representation—knowing that some parts
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
        assert topic_type == TopicManager.AGENT_TOPIC, f"Unexpected topic type in subject: {subject}"

        def none_if_wildcard(value: str) -> Optional[str]:
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
