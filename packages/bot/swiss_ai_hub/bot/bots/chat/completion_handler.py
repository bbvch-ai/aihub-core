import asyncio
import logging
import re
from asyncio import Event, Task
from collections.abc import AsyncGenerator
from typing import Any

from microsoft_agents.activity import Activity, ActivityTypes, Entity
from microsoft_agents.activity.teams import TeamsChannelAccount
from microsoft_agents.hosting.core import TeamsConnectorClient, TurnContext
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

from swiss_ai_hub.bot.bots.chat.content_extractor import ContentExtractor
from swiss_ai_hub.bot.persistence.entities.conversation_entity import Content, ConversationEntity, Message
from swiss_ai_hub.bot.persistence.entities.path_entity import PathEntity

logger = logging.getLogger(__name__)


class CompletionHandler:
    """
    Strategy pattern for handling different types of completions.

    This abstract base class defines the interface for handling
    chat completions, whether streaming or non-streaming.
    """

    @staticmethod
    async def get_completion(**kwargs) -> str:
        """Get a chat completion as a single response."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    async def get_stream_completion(**kwargs) -> AsyncGenerator[str]:
        """Get a chat completion as a stream of chunks."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def get_system_message(turn_context: TurnContext, path: str) -> Message | None:
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
        system_message: str | None = PathEntity.get_system_message_by_path(path)
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
    async def resolve_user_email(turn_context: TurnContext) -> str:
        """
        Resolve the user's real email address from a Bot Framework activity.

        Teams stores the *display name* (e.g. `John Doe`) in `from_property.name`, so the email
        must be fetched from the Teams connector. The display name is only a usable fallback when
        it already is an email (emulator / dev channels).
        """
        user_id = turn_context.activity.from_property.id

        connector_client = turn_context.turn_state.get("ConnectorClient")
        if user_id and isinstance(connector_client, TeamsConnectorClient):
            teams_account: TeamsChannelAccount = await connector_client.get_conversation_member(
                turn_context.activity.conversation.id, user_id
            )
            if teams_account.email is not None:
                return teams_account.email

        fallback = turn_context.activity.from_property.name
        if fallback and "@" in fallback:
            return fallback

        raise ValueError(
            f"Could not determine email for user '{turn_context.activity.from_property.name}'. "
            "Ensure the user has logged in via OAuth2 before using the bot."
        )

    @staticmethod
    async def resolve_user_identity(turn_context: TurnContext) -> UserIdentity:
        """
        Resolve the Keycloak-backed identity for the user behind the given activity.

        Shared by every completion handler so the agent and OpenAI bots cannot drift apart.
        """
        user_email = await CompletionHandler.resolve_user_email(turn_context)
        keycloak_user = await KeycloakAdminService.find_user_by_email(user_email)
        if not keycloak_user:
            raise ValueError(f"User with email '{user_email}' not found in Keycloak")
        realm_roles = await KeycloakAdminService.get_user_realm_roles(keycloak_user.id)
        tenant = await AuthHandler.get_active_tenant_for_user(keycloak_user.id)
        return UserIdentity(
            id=keycloak_user.id,
            name=keycloak_user.name,
            email=keycloak_user.email,
            roles=UserTenantRoleEntity.get_roles_for_user_in_tenant(keycloak_user.id, tenant.id),
            acting_within_tenant=tenant,
            is_sys_admin=SYS_ADMIN_ROLE in realm_roles,
        )

    @staticmethod
    def handle_teams_message(turn_context: TurnContext) -> TurnContext | None:
        is_direct_message: bool = CompletionHandler._is_teams_direct_message(turn_context)
        return CompletionHandler._handle_message(turn_context, is_direct_message)

    @staticmethod
    def _is_teams_direct_message(turn_context: TurnContext) -> bool:
        channel_data: dict[str, Any] = turn_context.activity.channel_data
        # Teams channel messages have a 'channel' property in channel_data
        return channel_data is None or channel_data.get("channel") is None

    @staticmethod
    def handle_slack_message(turn_context: TurnContext) -> TurnContext | None:
        is_channel_message = CompletionHandler._is_slack_channel_message(turn_context)

        if is_channel_message:
            turn_context = CompletionHandler._update_slack_turn_context(turn_context)

        is_direct_message = CompletionHandler._is_slack_direct_message(turn_context)
        return CompletionHandler._handle_message(turn_context, is_direct_message)

    @staticmethod
    def _is_slack_channel_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+$")
        return channel_id_regex.match(conversation_id) is not None

    @staticmethod
    def _is_slack_direct_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        dm_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:D[0-9A-Z]+:\d+[.]\d+$")
        return dm_id_regex.match(conversation_id) is not None

    @staticmethod
    def _handle_message(turn_context: TurnContext, is_direct_message: bool) -> TurnContext | None:
        is_mentioned: bool = CompletionHandler._is_bot_mentioned(turn_context)
        is_bot_thread: bool = CompletionHandler._is_mentioned_in_conversation(turn_context)
        if not is_direct_message and is_mentioned:
            CompletionHandler._mark_conversation_as_mentioned(turn_context)
        if not is_direct_message and not is_mentioned and not is_bot_thread:
            return None
        return turn_context

    @staticmethod
    def _is_bot_mentioned(turn_context: TurnContext) -> bool:
        mentions: list[Entity] = turn_context.activity.get_mentions()
        return any(
            mention.additional_properties["mentioned"]["id"] == turn_context.activity.recipient.id
            for mention in mentions
        )

    @staticmethod
    def _update_slack_turn_context(turn_context: TurnContext):
        """
        ### What
        1. Change the conversation id to refer to the message *thread* in Slack.
        2. Fetch all messages from the channel and add them to the context.

        ### Why
        1. The Bot should always respond in the same thread as the user's message.
        2. The Bot should have all channel messages to understand the conversation context.
        """
        channel_conversation_id: str = turn_context.activity.conversation.id
        bot_id: str = turn_context.activity.recipient.id
        channel_data = turn_context.activity.channel_data
        ts: str = channel_data["SlackMessage"]["event"]["ts"]
        turn_context.activity.conversation.id = channel_conversation_id + f":{ts}"
        parent_messages: list[Message] = CompletionHandler.get_messages_by_conversation_id(
            channel_conversation_id, bot_id
        )
        CompletionHandler._add_messages_to_conversation(turn_context, parent_messages)
        return turn_context

    @staticmethod
    def _mark_conversation_as_mentioned(turn_context: TurnContext):
        conversation_id: str = turn_context.activity.conversation.id
        bot_id: str = turn_context.activity.recipient.id
        ConversationEntity.set_conversation_is_mentioned(
            conversation_id=conversation_id, bot_id=bot_id, is_mentioned=True
        )

    @staticmethod
    def _is_mentioned_in_conversation(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        bot_id: str = turn_context.activity.recipient.id
        return ConversationEntity.get_conversation_is_mentioned(conversation_id, bot_id)

    @staticmethod
    def delete_conversation_if_exists(turn_context: TurnContext):
        conversation_id: str = turn_context.activity.conversation.id
        bot_id: str = turn_context.activity.recipient.id
        ConversationEntity.delete_conversation_if_exists(conversation_id, bot_id)

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
        return CompletionHandler._add_messages_to_conversation(turn_context, user_message)

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
            content=ContentExtractor.extract_content_from_activity(
                path=path, activity=Activity(text=message, type=ActivityTypes.message)
            ),
            role=turn_context.activity.recipient.role or "bot",
            name=turn_context.activity.recipient.name,
        )
        return CompletionHandler._add_messages_to_conversation(turn_context, bot_message)

    @staticmethod
    def _add_messages_to_conversation(
        turn_context: TurnContext,
        messages: list[Message] | Message,
    ) -> ConversationEntity:
        """
        ### What
        - Add the given messages to the persisted conversation.

        ### Why
        - The conversation must be persisted to keep the context, because past messages cannot be retrieved
        using from the Bot Framework.
        """
        conversation_id = turn_context.activity.conversation.id
        bot_id = turn_context.activity.recipient.id
        messages = messages if isinstance(messages, list) else [messages]
        return ConversationEntity.add_messages_to_conversation(
            conversation_id=conversation_id,
            bot_id=bot_id,
            messages=messages,
        )

    @staticmethod
    def get_messages_by_conversation_id(
        conversation_id: str,
        bot_id: str,
    ) -> list[Message]:
        """
        ### What
        - Get all messages from the persisted conversation.

        ### Why
        - To add the messages to the context of the conversation.
        """
        return list(ConversationEntity.get_messages_by_conversation_id(conversation_id, bot_id) or [])

    @staticmethod
    async def send_response_stream(
        turn_context: TurnContext,
        response_generator: AsyncGenerator[str],
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
            _activity: Activity | None = None,
            _sent_text: str = "",
        ) -> tuple[Activity | None, str]:
            if not _buffer:
                return _activity, _sent_text
            if _activity is None:
                _response = await _turn_context.send_activity(_buffer)
                return Activity(id=_response.id, text=_buffer, type=ActivityTypes.message), ""

            _activity.text = _buffer
            try:
                await _turn_context.update_activity(_activity)
                return _activity, ""
            except Exception as e:
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

    @staticmethod
    async def send_typing_activity(
        turn_context: TurnContext,
        signal: Event,
        t: LocaleHandler,
        timeout_seconds: int = 60,
    ):
        # Calculate iterations (2 seconds per activity)
        iterations = timeout_seconds // 2

        for _ in range(iterations):
            if signal.is_set():
                break
            await turn_context.send_activity(Activity(type=ActivityTypes.typing))
            await asyncio.sleep(2)

        if not signal.is_set():
            logger.exception(f"Timeout while waiting for a response to Activity:\n{turn_context.activity}")
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    text=t("bot.error.response_timeout"),
                )
            )

    @staticmethod
    async def handle_exception(
        turn_context: TurnContext,
        exception: Exception,
        typing_task: Task,
        typing_stop_signal: Event,
        t: LocaleHandler,
    ) -> str:
        logger.exception(f"Exception: {exception}\nTurnContext: {turn_context}")
        typing_stop_signal.set()
        await typing_task
        response = t("bot.error.generic_error")
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                text=response,
            )
        )
        return response
