from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_chat_response_event import (
    HumanInTheLoopChatResponseEvent,
)
from swiss_ai_hub.core.events.agent.hitl.timeout.human_in_the_loop_timeout_event import HumanInTheLoopTimeoutEvent
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic


class HumanInTheLoopChat:
    """Helper for triggering chat-style HITL steps within a workflow.

    Unlike input/confirmation types that show popup dialogs, chat requests appear
    as regular chat messages. The user responds by typing a normal chat message.
    """

    request = HumanInTheLoopChatRequestEvent
    response = HumanInTheLoopChatResponseEvent
    timeout = HumanInTheLoopTimeoutEvent

    @classmethod
    def invoke(cls, question: str, timeout_seconds: float | None = None) -> HumanInTheLoopChatRequestEvent:
        """Create a request for chat-style input from a human operator."""
        return cls.request(
            question=question,
            timeout_seconds=timeout_seconds,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
