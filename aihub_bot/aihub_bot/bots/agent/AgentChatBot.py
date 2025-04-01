import asyncio
from asyncio import Event, Task

from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from botbuilder.core import ActivityHandler, TurnContext
from botframework.connector import Channels
from nats.aio.client import Client as NATS
from typing_extensions import override

from aihub_bot.routes.agent.AgentChatService import AgentChatService


class AgentChatBot(ActivityHandler):
    """
    ### What
    - Handle incoming chat messages directed at an Agent defined by `agent_class` and `agent_id`.
    - Responds with a single `Activity` containing the answer of the Agent.

    ### Why
    - The Agent can be reached over multiple channels (e.g. Slack, Teams, ...).
    - Compared to the `OpenaiChatBot`, Agents can have advanced functionality (e.g. RAG).
    """

    def __init__(
        self, nc: NATS, external_event_distributor: ExternalEventDistributor, agent_class: str, agent_id: str, path: str
    ):
        self.nc = nc
        self.external_event_distributor = external_event_distributor
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.path = path

    @override
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        if (
            turn_context.activity.channel_id == Channels.ms_teams
            and turn_context.activity.members_added is not None
            and turn_context.activity.recipient.id in [member.id for member in turn_context.activity.members_added]
        ):
            AgentChatService.delete_conversation_if_exists(turn_context=turn_context)

        return super().on_conversation_update_activity(turn_context)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        typing_stop_signal = Event()
        typing: Task = asyncio.create_task(
            AgentChatService.send_typing_activity(
                turn_context=turn_context,
                signal=typing_stop_signal,
            )
        )

        AgentChatService.add_user_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
        )

        if turn_context.activity.channel_id == "slack":
            turn_context = AgentChatService.handle_slack_message(turn_context)
            if turn_context is None:
                return

        try:
            response = await AgentChatService.json_chat_completion(
                turn_context=turn_context,
                path=self.path,
                agent_class=self.agent_class,
                agent_id=self.agent_id,
                nc=self.nc,
                external_event_distributor=self.external_event_distributor,
                thread_id=ThreadEntity.to_thread_id(turn_context.activity.conversation.id),
            )

            typing_stop_signal.set()
            await typing
            await turn_context.send_activity(response)
        except Exception as e:
            await AgentChatService.handle_exception(
                turn_context=turn_context, exception=e, typing=typing, typing_stop_signal=typing_stop_signal
            )

        AgentChatService.add_bot_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
            message=response,
        )
