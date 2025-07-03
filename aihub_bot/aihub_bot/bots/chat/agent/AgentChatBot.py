from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from nats.aio.client import Client as NATS

from aihub_bot.bots.chat.agent.AgentCompletionHandler import AgentCompletionHandler
from aihub_bot.bots.chat.BaseChatBot import BaseChatBot


class AgentChatBot(BaseChatBot):
    def __init__(
        self,
        nc: NATS,
        external_event_distributor: ExternalAgentEventDistributor,
        agent_class: str,
        agent_id: str,
        path: str,
        typing_timeout_seconds: int = 60,
    ):
        super().__init__(
            path=path,
            completion_handler=AgentCompletionHandler(),
            handler_kwargs={
                "agent_class": agent_class,
                "agent_id": agent_id,
                "nc": nc,
                "external_event_distributor": external_event_distributor,
            },
            typing_timeout_seconds=typing_timeout_seconds,
        )
