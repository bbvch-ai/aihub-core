import asyncio
from asyncio import Event, Task
from typing import Type, Dict, Any

from botbuilder.core import ActivityHandler, TurnContext
from botframework.connector import Channels
from typing_extensions import override

from aihub_bot.bots.CompletionHandler import CompletionHandler


class BaseChatBot(ActivityHandler):
    """
    Base chatbot class that handles common functionality for all bots.

    This class implements the shared logic for all chatbots, including:
    - Handling conversation updates
    - Processing user messages
    - Managing typing indicators
    - Error handling
    - Message persistence
    """

    def __init__(
        self,
        path: str,
        completion_handler: CompletionHandler,
        handler_kwargs: Dict[str, Any],
    ):
        self.path = path
        self.completion_handler = completion_handler
        self.handler_kwargs = handler_kwargs

    @override
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """
        In Microsoft Teams, it is not possible to start a new conversation.
        When a user wants to start a new conversation, they need to delete the previous one.
        The conversation ID stays the same and the only way that the bot can know that a new conversation has started
        is when the bot is added to the conversation again.
        """
        if (
            turn_context.activity.channel_id == Channels.ms_teams
            and turn_context.activity.members_added is not None
            and turn_context.activity.recipient.id in [member.id for member in turn_context.activity.members_added]
        ):
            self.completion_handler.delete_conversation_if_exists(turn_context=turn_context)

        return await super().on_conversation_update_activity(turn_context)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        """Process the main message flow with stream=False by default."""
        await self._process_message(turn_context, is_streaming=False)

    async def _process_message(self, turn_context: TurnContext, is_streaming: bool = False):
        # Start typing indicator
        typing_stop_signal = Event()
        typing_task: Task = asyncio.create_task(
            self.completion_handler.send_typing_activity(
                turn_context=turn_context,
                signal=typing_stop_signal,
            )
        )

        # Persist user message
        self.completion_handler.add_user_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
        )

        # Handle Slack-specific message formatting
        if turn_context.activity.channel_id == "slack":
            turn_context = self.completion_handler.handle_slack_message(turn_context)
            if turn_context is None:
                return

        # Get response from completion handler
        try:
            response = await self._respond(
                turn_context=turn_context,
                typing_stop_signal=typing_stop_signal,
                typing_task=typing_task,
                is_streaming=is_streaming,
            )

        except Exception as e:
            # Handle exceptions
            response = await self.completion_handler.handle_exception(
                turn_context=turn_context,
                exception=e,
                typing_task=typing_task,
                typing_stop_signal=typing_stop_signal,
            )

        # Persist bot response
        self.completion_handler.add_bot_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
            message=response,
        )

    async def _respond(
        self,
        turn_context: TurnContext,
        typing_stop_signal: Event,
        typing_task: Task,
        is_streaming: bool = False,
    ) -> str:
        if is_streaming:
            # Get streaming response
            response_generator = await self.completion_handler.get_stream_completion(
                service=self.completion_handler, turn_context=turn_context, path=self.path, **self.handler_kwargs
            )

            # Stop typing indicator
            typing_stop_signal.set()
            await typing_task

            # Send streaming response
            return await self.completion_handler.send_response_stream(
                turn_context=turn_context,
                response_generator=response_generator,
            )
        else:
            # Get json response
            response = await self.completion_handler.get_completion(
                service=self.completion_handler, turn_context=turn_context, path=self.path, **self.handler_kwargs
            )

            # Stop typing indicator
            typing_stop_signal.set()
            await typing_task

            # Send json response
            await turn_context.send_activity(response)
            return response
