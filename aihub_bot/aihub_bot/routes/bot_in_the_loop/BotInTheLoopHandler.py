from collections.abc import Callable
from typing import Annotated

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoopRequestEvent
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig
from aihub_lib.nats.topics import AgentInstanceTopic
from botbuilder.core import TurnContext
from botbuilder.schema import ChannelAccount, ConversationAccount, ConversationReference
from botframework.connector import Channels
from cachetools import TTLCache
from fastapi import Request
from pydantic import BaseModel, Field

from aihub_bot.persistence.entities.PathEntity import PathEntity
from aihub_bot.routes.bot_in_the_loop.SlackUtils import SlackIds, SlackUtils
from aihub_bot.routes.RoutesService import RoutesService


class BotInTheLoopThread(BaseModel):
    thread_id: Annotated[str, Field(description="The ID of the thread in which the bot-in-the-loop requests are sent.")]
    conversation_id: Annotated[
        str,
        Field(
            description="The conversation ID where messages are sent to. For Slack: BotID:TeamID:ChannelID. For Teams: the channel (thread) conversation ID (e.g., 19:...@thread.tacv2)."
        ),
    ]
    thread_identifier: Annotated[
        str | None,
        Field(
            description="The Slack thread timestamp or the Teams message ID used to identify the specific thread.",
        ),
    ] = None
    last_request_event: Annotated[
        BotInTheLoopRequestEvent, Field(description="The last bot-in-the-loop request event sent in this thread.")
    ]


class BotInTheLoopHandler:
    CONTROLLER_PATH: str = "/bot_in_the_loop"
    ENDPOINT_PATH: str = "/response"

    # Cache TTL of 30 days
    CACHE_TTL_SECONDS = 60 * 60 * 24 * 30

    def __init__(self):
        self.threads: dict[str, BotInTheLoopThread] = {}
        self.path: str = f"/api/v1{self.CONTROLLER_PATH}{self.ENDPOINT_PATH}"
        # Use TTLCache with max size of 100 entries
        self.slack_ids_cache = TTLCache(maxsize=100, ttl=self.CACHE_TTL_SECONDS)

    async def handle_event(self, event: BaseEvent, _: AgentInstanceTopic):
        if event.is_bitl_request_event:
            await self._handle_bot_in_the_loop_request(event)
        else:
            return

    async def _get_slack_ids(self, path: str) -> SlackIds:
        """Get bot_id and team_id using the Slack auth.test API."""
        # Check cache first
        if path in self.slack_ids_cache:
            return self.slack_ids_cache[path]

        # Get the Slack token from the path entity
        slack_token = PathEntity.get_slack_token_by_path(path)
        if not slack_token:
            raise ValueError(f"No Slack token found for path {path}")

        # Use the SlackUtils to get the IDs
        slack_ids = SlackUtils.get_slack_ids(slack_token)

        # Cache the result for future use
        self.slack_ids_cache[path] = slack_ids

        return slack_ids

    async def _handle_bot_in_the_loop_request(
        self,
        event: BotInTheLoopRequestEvent,
    ):
        thread_id = event.topic.thread_id
        question = event.question

        if event.slack_channel_id is not None:
            await self._handle_bot_in_the_loop_request_in_slack(event, thread_id, question)

        elif event.teams_config is not None:
            await self._handle_bot_in_the_loop_request_in_teams(event, thread_id, question)

        else:
            raise ValueError("Either Slack channel or Teams channel must be provided")

    def _update_or_create_thread(
        self, thread_id: str, conversation_id: str, event: BotInTheLoopRequestEvent
    ) -> BotInTheLoopThread:
        if thread_id in self.threads:
            self.threads[thread_id].last_request_event = event
        else:
            self.threads[thread_id] = BotInTheLoopThread(
                thread_id=thread_id, conversation_id=conversation_id, last_request_event=event
            )
        return self.threads[thread_id]

    @staticmethod
    def _build_conversation_id_with_thread_identifier(thread: BotInTheLoopThread, channel: Channels) -> str:
        conversation_id = thread.conversation_id
        if thread.thread_identifier:
            if channel == Channels.slack:
                conversation_id += f":{thread.thread_identifier}"
            elif channel == Channels.ms_teams:
                conversation_id += f";messageid={thread.thread_identifier}"

        return conversation_id

    async def _send_bot_in_the_loop_message(
        self,
        conversation_reference: ConversationReference,
        question: str,
        thread: BotInTheLoopThread,
    ):
        adapter = RoutesService.get_adapter(self.path)
        await adapter.continue_conversation(
            bot_app_id=RoutesService.get_credentials(self.path).APP_ID,
            reference=conversation_reference,
            callback=self._bot_in_the_loop_callback(question, thread),
        )

    async def _handle_bot_in_the_loop_request_in_teams(
        self,
        event: BotInTheLoopRequestEvent,
        thread_id: str,
        question: str,
    ):
        teams_config: TeamsConfig = event.teams_config

        thread = self._update_or_create_thread(thread_id, teams_config.channel_id, event)

        conversation_id = self._build_conversation_id_with_thread_identifier(thread, Channels.ms_teams)

        conversation = ConversationReference(
            channel_id=Channels.ms_teams.value,
            conversation=ConversationAccount(
                id=conversation_id,
                conversation_type="channel",
            ),
            service_url=f"https://smba.trafficmanager.net/emea/{teams_config.tenant_id}/",
            bot=ChannelAccount(
                id=teams_config.bot_id,
            ),
        )

        await self._send_bot_in_the_loop_message(conversation, question, thread)

    async def _handle_bot_in_the_loop_request_in_slack(
        self,
        event: BotInTheLoopRequestEvent,
        thread_id: str,
        question: str,
    ):
        slack_ids = await self._get_slack_ids(self.path)
        base_conversation_id = f"{slack_ids.bot_id}:{slack_ids.team_id}:{event.slack_channel_id}"

        thread = self._update_or_create_thread(thread_id, base_conversation_id, event)

        conversation_id = self._build_conversation_id_with_thread_identifier(thread, Channels.slack)

        bot_team_id = f"{slack_ids.bot_id}:{slack_ids.team_id}"

        conversation = ConversationReference(
            channel_id=Channels.slack.value,
            conversation=ConversationAccount(
                id=conversation_id,
            ),
            service_url="https://europe.slack.botframework.com",
            bot=ChannelAccount(id=bot_team_id),
        )

        await self._send_bot_in_the_loop_message(conversation, question, thread)

    @staticmethod
    def _bot_in_the_loop_callback(question: str, thread: BotInTheLoopThread) -> Callable:
        async def callback(turn_context: TurnContext):
            response = await turn_context.send_activity(question)
            if response and hasattr(response, "id") and thread.thread_identifier is None:
                thread.thread_identifier = response.id

        return callback

    @staticmethod
    def use_bot_in_the_loop_handler(request: Request) -> "BotInTheLoopHandler":
        return request.app.state.bot_in_the_loop_handler
