import asyncio
from asyncio import Event, Task
from typing import Any, override

from microsoft_agents.activity import Activity, ActivityTypes, Channels
from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.utils import str_to_object_id

from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler
from swiss_ai_hub.bot.persistence.entities.conversation_entity import ConversationTracker


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
        handler_kwargs: dict[str, Any],
        typing_timeout_seconds: int = 60,
    ):
        self.path = path
        self.completion_handler = completion_handler
        self.handler_kwargs = handler_kwargs
        self.locale_handler = LocaleHandler()
        self.typing_timeout_seconds = typing_timeout_seconds

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
            and turn_context.activity.channel_data.get("team") is None
        ):
            conversation_id = turn_context.activity.conversation.id
            bot_id = turn_context.activity.recipient.id
            ConversationTracker.mark_explicitly_deleted(conversation_id, bot_id)

            self.completion_handler.delete_conversation_if_exists(turn_context=turn_context)

        return await super().on_conversation_update_activity(turn_context)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        """Process the main message flow with stream=False by default."""
        await self._process_message(turn_context, is_streaming=False)

    def _get_locale_handler(self, turn_context: TurnContext) -> LocaleHandler:
        if turn_context.activity.locale:
            locale = self.locale_handler.get_locale(turn_context.activity.locale.split("-")[0])
        else:
            locale = self.locale_handler.DEFAULT_LOCALE
        return self.locale_handler.in_locale(locale)

    async def _process_message(self, turn_context: TurnContext, is_streaming: bool = False):
        locale_handler = self._get_locale_handler(turn_context)
        conversation_id = turn_context.activity.conversation.id
        bot_id = turn_context.activity.recipient.id

        if (
            ConversationTracker.should_show_expiration_message(conversation_id, bot_id)
            and turn_context.activity.type == "message"
        ):
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text="This conversation has expired after 1 month of inactivity. "
                    "Your previous messages are no longer available.",
                )
            )

        # Always track this conversation ID
        ConversationTracker.track_conversation(conversation_id, bot_id)

        self.completion_handler.add_user_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
        )

        if turn_context.activity.channel_id == Channels.slack:
            turn_context = self.completion_handler.handle_slack_message(turn_context)
            if turn_context is None:
                return

        if turn_context.activity.channel_id == Channels.ms_teams:
            turn_context = self.completion_handler.handle_teams_message(turn_context)
            if turn_context is None:
                return

        typing_stop_signal = Event()
        typing_task: Task = asyncio.create_task(
            self.completion_handler.send_typing_activity(
                turn_context=turn_context,
                signal=typing_stop_signal,
                t=locale_handler,
                timeout_seconds=self.typing_timeout_seconds,
            )
        )

        try:
            response = await self._respond(
                turn_context=turn_context,
                typing_stop_signal=typing_stop_signal,
                typing_task=typing_task,
                is_streaming=is_streaming,
            )

        except Exception as e:
            response = await self.completion_handler.handle_exception(
                turn_context=turn_context,
                exception=e,
                typing_task=typing_task,
                typing_stop_signal=typing_stop_signal,
                t=locale_handler,
            )

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
            response_generator = await self.completion_handler.get_stream_completion(
                turn_context=turn_context,
                path=self.path,
                thread_id=str_to_object_id(turn_context.activity.conversation.id),
                display_id=str_to_object_id(turn_context.activity.id),
                **self.handler_kwargs,
            )

            typing_stop_signal.set()
            await typing_task

            return await self.completion_handler.send_response_stream(
                turn_context=turn_context,
                response_generator=response_generator,
            )
        else:
            response = await self.completion_handler.get_completion(
                turn_context=turn_context,
                path=self.path,
                thread_id=str_to_object_id(turn_context.activity.conversation.id),
                display_id=str_to_object_id(turn_context.activity.id),
                **self.handler_kwargs,
            )

            typing_stop_signal.set()
            await typing_task

            await turn_context.send_activity(response)
            return response
