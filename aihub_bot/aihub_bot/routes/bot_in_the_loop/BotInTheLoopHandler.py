from typing import Callable, Dict, Optional, Tuple

from aihub_bot.persistence.entities.PathEntity import PathEntity
from aihub_bot.routes.bot_in_the_loop.SlackUtils import SlackUtils
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoopRequestEvent
from aihub_lib.nats.topics import AgentTopic
from botbuilder.core import TurnContext
from botbuilder.schema import ChannelAccount, ConversationAccount, ConversationReference
from fastapi import Request
from pydantic import BaseModel, Field

from aihub_bot.routes.RoutesService import RoutesService


class BotInTheLoopThread(BaseModel):
    thread_id: str = Field(..., description="The ID of the thread in which the bot-in-the-loop requests are sent.")
    slack_channel_id: str = Field(
        ..., description="The full Slack channel ID (format: BotID:TeamID:ChannelID) where messages are sent to."
    )
    slack_thread_id: Optional[str] = Field(
        None,
        description="The ID of the Slack thread where the bot-in-the-loop requests are sent to and responses are received from.",
    )
    last_request_event: BotInTheLoopRequestEvent = Field(
        ..., description="The last bot-in-the-loop request event sent in this thread."
    )


class BotInTheLoopHandler:
    CONTROLLER_PATH: str = "/bot_in_the_loop"
    ENDPOINT_PATH: str = "/response"

    def __init__(self):
        self.threads: Dict[str, BotInTheLoopThread] = {}
        self.path: str = f"/api/v1{self.CONTROLLER_PATH}{self.ENDPOINT_PATH}"
        # Cache for Slack IDs to avoid repeated API calls
        self.slack_ids_cache: Dict[str, Tuple[str, str]] = {}

    async def handle_event(self, event: BaseEvent, _: AgentTopic):
        if event.is_bitl_request_event:
            await self._handle_bot_in_the_loop_request(event)
        else:
            return

    async def _get_slack_ids(self, path: str) -> Optional[Tuple[str, str]]:
        """Get bot_id and team_id using the Slack auth.test API."""
        # Check cache first
        if path in self.slack_ids_cache:
            return self.slack_ids_cache[path]

        # Get the Slack token from the path entity
        slack_token = PathEntity.get_slack_token_by_path(path)
        if not slack_token:
            return None

        # Use the SlackUtils to get the IDs
        slack_ids = await SlackUtils.get_slack_ids(slack_token)
        if slack_ids:
            # Cache the result for future use
            self.slack_ids_cache[path] = slack_ids

        return slack_ids

    async def _handle_bot_in_the_loop_request(
        self,
        event: BotInTheLoopRequestEvent,
    ):
        thread_id = event.topic.thread_id
        question = event.question

        # Get the Slack IDs (bot_id and team_id)
        slack_ids = await self._get_slack_ids(self.path)
        if not slack_ids:
            raise ValueError("Failed to get Slack bot_id and team_id. Check the Slack token.")

        bot_id, team_id = slack_ids
        # Create the full channel ID format with just the channel ID provided
        channel_id = f"{bot_id}:{team_id}:{event.conversation_id}"

        if thread_id in self.threads:
            # Handle the case where the thread already exists
            # Update the existing thread with the new request event
            self.threads[thread_id].last_request_event = event
        else:
            # Handle the case where the thread does not exist
            # Create a new thread and add it to the threads dictionary
            self.threads[thread_id] = BotInTheLoopThread(
                thread_id=thread_id, slack_channel_id=channel_id, last_request_event=event
            )

        # Create conversation reference for the adapter
        conversation_id = self.threads[thread_id].slack_channel_id
        if self.threads[thread_id].slack_thread_id:
            conversation_id += f":{self.threads[thread_id].slack_thread_id}"

        bot_team_id = f"{bot_id}:{team_id}"

        conversation = ConversationReference(
            channel_id="slack",
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
            if turn_context.activity.channel_id == "slack":
                response = await turn_context.send_activity(question)
                # Update the slack_thread_id in the thread mapping
                if response and hasattr(response, "id") and thread.slack_thread_id is None:
                    thread.slack_thread_id = response.id
            else:
                raise NotImplementedError("Only Slack channel is supported")

        return callback

    @staticmethod
    def use_bot_in_the_loop_handler(request: Request) -> "BotInTheLoopHandler":
        return request.app.state.bot_in_the_loop_handler
