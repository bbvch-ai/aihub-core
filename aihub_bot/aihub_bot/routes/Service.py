import logging
import re
from typing import Optional, List, AsyncGenerator

from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, Entity
from fastapi import Request

from aihub_bot.persistence.entities.ConversationEntity import Message, ConversationEntity
from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity
from aihub_lib.routes.chat.ChatService import ChatService

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

        ### Why
        - The system message can be configured in the database.
        - The LLM and Agents should get instructions on how to interact with the user.
        - The instructions should be personalized with the user's name.
        """
        system_message: Optional[str] = PathEntity.get_system_message_by_path(path)
        if system_message is None:
            return None
        username = turn_context.activity.from_property.name
        system_message = system_message.format(username=username)
        return Message(
            user_id="system",
            content=system_message,
            role="system",
        )

    @staticmethod
    def is_slack_channel_message(turn_context: TurnContext) -> bool:
        """
        ### What
        - Check if the message is from a Slack channel.

        ### Why
        - Slack channel messages need special handling.
        """
        assert turn_context.activity.channel_id == "slack"
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]{10}:T[0-9A-Z]{10}:C[0-9A-Z]{10}$")
        return channel_id_regex.match(conversation_id) is not None

    @staticmethod
    def is_bot_mentioned(turn_context: TurnContext) -> bool:
        """
        ### What
        - Check if the bot is mentioned in the user's message.

        ### Why
        - The Bot may only respond if it is mentioned.
        """
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
    def add_user_message_to_conversation(turn_context: TurnContext) -> ConversationEntity:
        """
        ### What
        - Add the user message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role or "user",
        )
        return Service.add_messages_to_conversation(turn_context, user_message)

    @staticmethod
    def add_bot_message_to_conversation(turn_context: TurnContext, message: str) -> ConversationEntity:
        """
        ### What
        - Add the bot message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=message,
            role=turn_context.activity.recipient.role or "bot",
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
        return ConversationEntity.get_messages_by_conversation_id(conversation_id)

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
        first_chunk = await anext(response_generator, "No response from the agent.")
        message = await turn_context.send_activity(first_chunk)
        activity = Activity(id=message.id, text=first_chunk)
        async for chunk in response_generator:
            if chunk is None:
                break
            activity.text += chunk
            await turn_context.update_activity(activity)
        return activity.text
