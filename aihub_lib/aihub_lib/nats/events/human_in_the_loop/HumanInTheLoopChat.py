from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopChatRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopChatResponseEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoopChat:
    """Helper for triggering chat-style HITL steps within a workflow.

    Unlike input/confirmation types that show popup dialogs, chat requests appear
    as regular chat messages. The user responds by typing a normal chat message.
    """

    request = HumanInTheLoopChatRequestEvent
    response = HumanInTheLoopChatResponseEvent

    @classmethod
    def invoke(cls, question: str) -> HumanInTheLoopChatRequestEvent:
        """Create a request for chat-style input from a human operator."""
        return cls.request(
            question=question,
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=cls.response.event_name_from_class(),
            ),
        )
