import asyncio
import logging
import re
from asyncio import Task
from typing import AsyncGenerator, List, Optional, Tuple

from aihub_lib.routes.chat.ChatService import ChatService
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes, Entity, ErrorResponseException
from fastapi import Request

from aihub_bot.persistence.entities.ConversationEntity import Content, ConversationEntity, Message
from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity
from .ContentExtractor import ContentExtractor

logger = logging.getLogger(__name__)


class Service(ChatService):
    """
    ### What
    - Shared functionality for all ChatControllers and ChatBots.
    """

    @staticmethod
    def get_path(request: Request) -> str:
        """
        ### What
        - Returns the path/endpoint of the request.

        ### Why
        - Each endpoint can be configured in the database.
        - The path is the key to access this configuration.
        - See `PathEntity`.
        """
        return str(request.url).replace(str(request.base_url), "/")

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        """
        ### What
        - Returns the adapter for the given path.

        ### Why
        - Each path has a unique set of credentials.
        - The credential is needed to verify that requests are coming from the correct bot service.
        """
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))

    @staticmethod
    def get_system_message(turn_context: TurnContext, path: str) -> Optional[Message]:
        """
        ### What
        - Returns the configured system message for the given path.
        - Replaces the placeholder `{username}` with the given username.
        - Replaces the placeholder `{assistant_name}` with the given assistant name.

        ### Why
        - The system message can be configured in the database.
        - The LLM and Agents should get instructions on how to interact with the user.
        - The instructions should be personalized with the user's name.
        """
        system_message: Optional[str] = PathEntity.get_system_message_by_path(path)
        if system_message is None:
            return None
        username = turn_context.activity.from_property.name
        assistant_name = turn_context.activity.recipient.name
        system_message = system_message.format(username=username)
        system_message = system_message.format(assistant_name=assistant_name)
        return Message(
            user_id="system",
            content=[Content(text=system_message, type="text")],
            role="system",
            name="system",
        )

    @staticmethod
    def handle_slack_message(turn_context: TurnContext) -> Optional[TurnContext]:
        is_direct_message = Service.is_slack_direct_message(turn_context)
        is_channel_message = Service.is_slack_channel_message(turn_context)
        is_mentioned = Service.is_bot_mentioned(turn_context)
        is_bot_thread = Service.is_mentioned_in_conversation(turn_context)

        if is_channel_message:
            turn_context = Service.update_slack_turn_context(turn_context)
            if is_mentioned:
                Service.mark_conversation_as_mentioned(turn_context)
        if not is_direct_message and not is_mentioned and not is_bot_thread:
            return None

        return turn_context

    @staticmethod
    def is_slack_channel_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+$")
        return channel_id_regex.match(conversation_id) is not None

    @staticmethod
    def is_slack_direct_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        dm_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:D[0-9A-Z]+:\d+[.]\d+$")
        return dm_id_regex.match(conversation_id) is not None

    @staticmethod
    def is_bot_mentioned(turn_context: TurnContext) -> bool:
        mentions: List[Entity] = turn_context.activity.get_mentions()
        return any(
            mention.additional_properties["mentioned"]["id"] == turn_context.activity.recipient.id
            for mention in mentions
        )

    @staticmethod
    def update_slack_turn_context(turn_context: TurnContext):
        """
        ### What
        1. Change the conversation id to refer to the message *thread* in Slack.
        2. Fetch all messages from the channel and add them to the context.

        ### Why
        1. The Bot should always respond in the same thread as the user's message.
        2. The Bot should have all channel messages to understand the conversation context.
        """
        channel_conversation_id: str = turn_context.activity.conversation.id
        channel_data = turn_context.activity.channel_data
        ts: str = channel_data["SlackMessage"]["event"]["ts"]
        turn_context.activity.conversation.id = channel_conversation_id + f":{ts}"
        parent_messages: List[Message] = Service.get_messages_by_conversation_id(channel_conversation_id)
        Service.add_messages_to_conversation(turn_context, parent_messages)
        return turn_context

    @staticmethod
    def mark_conversation_as_mentioned(turn_context: TurnContext):
        conversation_id: str = turn_context.activity.conversation.id
        ConversationEntity.set_conversation_is_mentioned(conversation_id=conversation_id, is_mentioned=True)

    @staticmethod
    def is_mentioned_in_conversation(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        return ConversationEntity.get_conversation_is_mentioned(conversation_id)

    @staticmethod
    def delete_conversation_if_exists(turn_context: TurnContext):
        conversation_id: str = turn_context.activity.conversation.id
        ConversationEntity.delete_conversation(conversation_id)

    @staticmethod
    def add_user_message_to_conversation(path: str, turn_context: TurnContext) -> ConversationEntity:
        """
        ### What
        - Add the user message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=ContentExtractor.extract_content_from_activity(path=path, activity=turn_context.activity),
            role=turn_context.activity.from_property.role or "user",
            name=turn_context.activity.from_property.name,
        )
        return Service.add_messages_to_conversation(turn_context, user_message)

    @staticmethod
    def add_bot_message_to_conversation(
        path: str,
        turn_context: TurnContext,
        message: str,
    ) -> ConversationEntity:
        """
        ### What
        - Add the bot message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=ContentExtractor.extract_content_from_activity(path=path, activity=Activity(text=message)),
            role=turn_context.activity.recipient.role or "bot",
            name=turn_context.activity.recipient.name,
        )
        return Service.add_messages_to_conversation(turn_context, bot_message)

    @staticmethod
    def add_messages_to_conversation(
        turn_context: TurnContext,
        messages: List[Message] | Message,
    ) -> ConversationEntity:
        """
        ### What
        - Add the given messages to the persisted conversation.

        ### Why
        - The conversation must be persisted to keep the context, because past messages cannot be retrieved
        using from the Bot Framework.
        """
        conversation_id = turn_context.activity.conversation.id
        messages = messages if isinstance(messages, list) else [messages]
        return ConversationEntity.add_messages_to_conversation(
            conversation_id=conversation_id,
            messages=messages,
        )

    @staticmethod
    def get_messages_by_conversation_id(
        conversation_id: str,
    ) -> List[Message]:
        """
        ### What
        - Get all messages from the persisted conversation.

        ### Why
        - To add the messages to the context of the conversation.
        """
        return list(ConversationEntity.get_messages_by_conversation_id(conversation_id) or [])

    @staticmethod
    async def send_response_stream(
        turn_context: TurnContext,
        response_generator: AsyncGenerator[str, None],
    ) -> str:
        """
        ### What
        - Send an initial Activity with the first chunk of the response.
        - Update the Activity with the next chunks of the response.

        ### Why
        - The response can be very long and should be sent in chunks.
        - The user can see the response while it is being generated.
        """

        async def _send_text(
            _turn_context: TurnContext,
            _buffer: str,
            _activity: Optional[Activity] = None,
            _sent_text: str = "",
        ) -> Tuple[Optional[Activity], str]:
            if not _buffer:
                return _activity, _sent_text
            if _activity is None:
                _response = await _turn_context.send_activity(_buffer)
                return Activity(id=_response.id, text=_buffer, type=ActivityTypes.message), ""

            _activity.text = _buffer
            try:
                await _turn_context.update_activity(_activity)
                return _activity, ""
            except ErrorResponseException as e:
                if "msg_too_long" in str(e):
                    new_text = _buffer.replace(_sent_text, "", 1)
                    _response = await _turn_context.send_activity(new_text)
                    return Activity(id=_response.id, text=new_text, type=ActivityTypes.message), _sent_text
                raise e

        response = await anext(response_generator, "No response from the agent.")
        task: Task = asyncio.create_task(_send_text(turn_context, response))

        buffer = response
        sent_text = response
        async for chunk in response_generator:
            if chunk is None:
                break
            buffer += chunk
            response += chunk
            if task.done():
                activity, used_buffer = task.result()
                buffer = buffer.replace(used_buffer, "", 1)
                task = asyncio.create_task(_send_text(turn_context, buffer, activity, sent_text))
                sent_text = buffer

        await task
        activity, used_buffer = task.result()
        buffer = buffer.replace(used_buffer, "", 1)
        await _send_text(turn_context, buffer, activity, sent_text)

        return response
