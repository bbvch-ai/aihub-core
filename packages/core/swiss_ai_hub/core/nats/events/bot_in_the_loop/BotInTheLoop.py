from swiss_ai_hub.core.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import BotInTheLoopRequestEvent
from swiss_ai_hub.core.nats.events.bot_in_the_loop.response.BotInTheLoopResponseEvent import BotInTheLoopResponseEvent
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class BotInTheLoop:
    """
    A helper for triggering bot-in-the-loop (HITL) steps within a workflow.
    The HITL pattern allows the system to pause execution and ask a bot operator for guidance
    or approval before proceeding.

    ### Why BotInTheLoop?
    In automated workflows, certain decisions or validations may be too sensitive or complex for
    the AI agent alone. HITL steps:
    - Pause at a critical point.
    - Ask a bot a question or request confirmation.
    - Resume execution once the bot response is received.

    This class:
    - Provides a convenient `invoke` method to create a `BotInTheLoopRequestEvent`.
    - Defines `request` and `response` attributes pointing to event classes representing HITL requests and responses.
    """

    request = BotInTheLoopRequestEvent
    response = BotInTheLoopResponseEvent

    @classmethod
    def invoke(cls, **kwargs):
        """
        Create a `BotInTheLoopRequestEvent` to prompt a bot for input.

        The `invoke` method constructs the request event and attaches a partial topic indicating where
        the corresponding `BotInTheLoopResponseEvent` should be directed. This ensures that once
        a bot responds, the workflow can resume from the correct point.
        """
        return cls.request(
            **kwargs,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=BotInTheLoopResponseEvent.__name__,
            ),
        )
