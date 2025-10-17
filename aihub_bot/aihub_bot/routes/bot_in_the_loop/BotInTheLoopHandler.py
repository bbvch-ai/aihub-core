from collections.abc import Callable
from typing import Annotated

from botframework.connector import Channels

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoopRequestEvent
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig
from aihub_lib.nats.topics import AgentInstanceTopic
from botbuilder.core import TurnContext
from botbuilder.schema import ChannelAccount, ConversationAccount, ConversationReference
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
            description="The full Slack conversation ID (format: BotID:TeamID:ChannelID) where messages are sent to."
        ),
    ]
    slack_thread_ts: Annotated[
        str | None,
        Field(
            description="The timestamp of the Slack thread that acts as an identifier "
            "for the Slack thread where the bot-in-the-loop request is sent to.",
        ),
    ] = None
    teams_message_id: Annotated[
        str | None,
        Field(
            description="The ID of the Teams message that acts as an identifier "
            "for the Teams thread where the bot-in-the-loop request is sent to.",
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

    async def _handle_bot_in_the_loop_request_in_teams(
        self,
        event: BotInTheLoopRequestEvent,
        thread_id: str,
        question: str,
    ):
        teams_config: TeamsConfig = event.teams_config

        if thread_id in self.threads:
            # Handle the case where the thread already exists
            # Update the existing thread with the new request event
            self.threads[thread_id].last_request_event = event
        else:
            # Handle the case where the thread does not exist
            # Create a new thread and add it to the threads dictionary
            self.threads[thread_id] = BotInTheLoopThread(
                thread_id=thread_id, conversation_id=teams_config.channel_id, last_request_event=event
            )

        conversation = ConversationReference(
            channel_id=Channels.ms_teams.value,
            conversation=ConversationAccount(
                id=teams_config.channel_id,
                conversation_type="channel",
            ),
            service_url=f"https://smba.trafficmanager.net/emea/{teams_config.tenant_id}/",
            bot=ChannelAccount(
                id=teams_config.bot_id,
            ),
        )
        adapter = RoutesService.get_adapter(self.path)
        await adapter.continue_conversation(
            bot_app_id=RoutesService.get_credentials(self.path).APP_ID,
            reference=conversation,
            callback=self._bot_in_the_loop_callback(question, self.threads[thread_id]),
        )

    async def _handle_bot_in_the_loop_request_in_slack(
        self,
        event: BotInTheLoopRequestEvent,
        thread_id: str,
        question: str,
    ):
        # Get the Slack IDs (bot_id and team_id)
        slack_ids = await self._get_slack_ids(self.path)

        # Create the full channel ID format with just the channel ID provided
        conversation_id = f"{slack_ids.bot_id}:{slack_ids.team_id}:{event.slack_channel_id}"

        if thread_id in self.threads:
            # Handle the case where the thread already exists
            # Update the existing thread with the new request event
            self.threads[thread_id].last_request_event = event
        else:
            # Handle the case where the thread does not exist
            # Create a new thread and add it to the threads dictionary
            self.threads[thread_id] = BotInTheLoopThread(
                thread_id=thread_id, conversation_id=conversation_id, last_request_event=event
            )

        # Create conversation reference for the adapter
        conversation_id = self.threads[thread_id].conversation_id
        if self.threads[thread_id].slack_thread_ts:
            conversation_id += f":{self.threads[thread_id].slack_thread_ts}"

        bot_team_id = f"{slack_ids.bot_id}:{slack_ids.team_id}"

        conversation = ConversationReference(
            channel_id=Channels.slack.value,
            conversation=ConversationAccount(
                id=conversation_id,
            ),
            service_url="https://europe.slack.botframework.com",
            bot=ChannelAccount(id=bot_team_id),
        )

        adapter = RoutesService.get_adapter(self.path)
        await adapter.continue_conversation(
            bot_app_id=RoutesService.get_credentials(self.path).APP_ID,
            reference=conversation,
            callback=self._bot_in_the_loop_callback(question, self.threads[thread_id]),
        )

    def _bot_in_the_loop_callback(self, question: str, thread: BotInTheLoopThread) -> Callable:
        async def callback(turn_context: TurnContext):
            # Send the question to the user in the Slack channel
            if turn_context.activity.channel_id == Channels.slack:
                response = await turn_context.send_activity(question)
                # Update the slack_thread_id in the thread mapping
                if response and hasattr(response, "id") and thread.slack_thread_ts is None:
                    thread.slack_thread_ts = response.id
            elif turn_context.activity.channel_id == Channels.ms_teams:
                response = await turn_context.send_activity(question)
                # Update the teams_message_id in the thread mapping
                if response and hasattr(response, "id") and thread.teams_message_id is None:
                    thread.teams_message_id = response.id
            else:
                raise NotImplementedError("Only Slack and Teams channels are supported")

        return callback

    @staticmethod
    def use_bot_in_the_loop_handler(request: Request) -> "BotInTheLoopHandler":
        return request.app.state.bot_in_the_loop_handler
