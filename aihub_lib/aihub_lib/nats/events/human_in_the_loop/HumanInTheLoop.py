from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import HumanInTheLoopResponseEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoop:
    """
    A helper for triggering human-in-the-loop (HITL) steps within a workflow.
    The HITL pattern allows the system to pause execution and ask a human operator for guidance
    or approval before proceeding.

    ### Why HumanInTheLoop?
    In automated workflows, certain decisions or validations may be too sensitive or complex for
    the AI agent alone. HITL steps:
    - Pause at a critical point.
    - Ask a human a question or request confirmation.
    - Resume execution once the human response is received.

    This class:
    - Provides a convenient `invoke` method to create a `HumanInTheLoopRequestEvent`.
    - Defines `request` and `response` attributes pointing to event classes representing HITL requests and responses.
    """

    request = HumanInTheLoopRequestEvent
    response = HumanInTheLoopResponseEvent

    @classmethod
    def invoke(cls, **kwargs):
        """
        Create a `HumanInTheLoopRequestEvent` to prompt a human for input.

        The `invoke` method constructs the request event and attaches a partial topic indicating where
        the corresponding `HumanInTheLoopResponseEvent` should be directed. This ensures that once
        a human responds, the workflow can resume from the correct point.
        """
        return cls.request(
            **kwargs,
            topic=PartialAgentTopic(
                event_type=TopicManager.CONTROL_EVENT,
                event_name=HumanInTheLoopResponseEvent.event_name_from_class(),
            ),
        )
