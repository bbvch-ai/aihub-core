from typing import Any

from aihub_lib.nats.events.expert_in_the_loop.request.ExpertInTheLoopRequestEvent import ExpertInTheLoopRequestEvent
from aihub_lib.nats.events.expert_in_the_loop.response.ExpertInTheLoopResponseEvent import ExpertInTheLoopResponseEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class ExpertInTheLoop:
    """
    A helper for triggering expert-in-the-loop steps within a workflow via the built-in GUI.

    The Expert-in-the-Loop pattern allows the system to pause execution and ask domain experts
    for guidance through a web-based interface, as an alternative to external platforms like
    Slack or Teams (Bot-in-the-Loop).

    ### Why ExpertInTheLoop?
    When automated workflows require domain expertise that cannot be provided by AI alone,
    Expert-in-the-Loop steps:
    - Pause at a critical point in the workflow.
    - Display a question to qualified experts through the platform's GUI.
    - Resume execution once an expert provides a response.

    This class:
    - Provides a convenient `invoke` method to create an `ExpertInTheLoopRequestEvent`.
    - Defines `request` and `response` attributes for event classes.
    """

    request = ExpertInTheLoopRequestEvent
    response = ExpertInTheLoopResponseEvent

    @classmethod
    def invoke(cls, **kwargs: Any) -> ExpertInTheLoopRequestEvent:
        """
        Create an `ExpertInTheLoopRequestEvent` to prompt an expert for input via the GUI.

        The `invoke` method constructs the request event and attaches a partial topic indicating
        where the corresponding `ExpertInTheLoopResponseEvent` should be directed. This ensures
        that once an expert responds, the workflow can resume from the correct point.
        """
        return cls.request(
            **kwargs,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=ExpertInTheLoopResponseEvent.__name__,
            ),
        )
