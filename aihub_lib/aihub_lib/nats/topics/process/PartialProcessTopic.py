from typing import Annotated, Self

from pydantic import Field

from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.Topic import Topic


class PartialProcessTopic(Topic):
    """
    Represents a partially qualified process event topic, where some fields may be unspecified.
    Wildcards (represented by "*") in the subject translate into None values here.

    ### Why PartialProcessTopic?
    Sometimes you deal with generic subscriptions to broad categories of events - like all display events
    or all events from a particular process class - without knowing the exact process_id, thread_id, or event_id.
    PartialProcessTopic captures this scenario, making it explicit which parts of the topic are defined
    and which remain open (None).
    """

    process_class: Annotated[str | None, Field(description="Process class or None if unspecified.")] = None
    process_id: Annotated[str | None, Field(description="Process ID or None if unspecified.")] = None
    process_walkthrough_id: Annotated[str | None, Field(description="Walkthrough ID or None if unspecified.")] = None
    event_type: Annotated[str | None, Field(description="Event type or None if unspecified.")] = None
    event_name: Annotated[str | None, Field(description="Event name or None if unspecified.")] = None
    event_id: Annotated[str | None, Field(description="Event ID or None if unspecified.")] = None

    @property
    def execution_context_id(self) -> str:
        return self.process_walkthrough_id

    @classmethod
    def from_subject(cls, subject: str) -> Self:
        """
        Constructs a PartialProcessTopic from a subject string that may contain wildcards.

        Use this when you have a subject and need a structured representation - knowing that some parts
        of the topic might be generalized (wildcards) rather than fully specified. This is common in
        subscription scenarios where you are not targeting a single event, but a category of events.
        """
        (
            topic_type,
            process_class,
            process_id,
            walkthrough_id,
            event_type,
            event_name,
            event_id,
        ) = subject.split(".")
        assert topic_type == ProcessTopicManager.PROCESS_TOPIC, f"Unexpected topic type in subject: {subject}"

        def none_if_wildcard(value: str) -> str | None:
            return value if value != "*" else None

        return cls(
            process_class=none_if_wildcard(process_class),
            process_id=none_if_wildcard(process_id),
            process_walkthrough_id=none_if_wildcard(walkthrough_id),
            event_type=none_if_wildcard(event_type),
            event_name=none_if_wildcard(event_name),
            event_id=none_if_wildcard(event_id),
        )

    def to_subject(self):
        return (
            f"{ProcessTopicManager.PROCESS_TOPIC}."
            f"{self.process_class or '*'}."
            f"{self.process_id or '*'}."
            f"{self.process_walkthrough_id or '*'}."
            f"{self.event_type or '*'}."
            f"{self.event_name or '*'}."
            f"{self.event_id or '*'}"
        )
