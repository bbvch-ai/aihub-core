import asyncio
import logging
import re
import unicodedata
from asyncio import Event, Task
from collections.abc import AsyncGenerator
from typing import override

import openai
from microsoft_agents.activity.teams import TeamsChannelAccount
from microsoft_agents.hosting.core import TeamsConnectorClient, TurnContext
from openai import APIStatusError, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ChatCompletionContentPartImageParam, ImageURL
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import LiteLLMService
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler
from swiss_ai_hub.bot.persistence.entities.conversation_entity import Content, Message

logger = logging.getLogger(__name__)


class OpenaiCompletionHandler(CompletionHandler):
    """
    Strategy for handling OpenAI completions.
    """

    @staticmethod
    async def get_completion(
        turn_context: TurnContext,
        path: str,
        model_name: str,
        **kwargs,
    ) -> str:
        chat_completion: ChatCompletion = await OpenaiCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            stream=False,
        )
        return chat_completion.choices[0].message.content

    @staticmethod
    async def get_stream_completion(
        turn_context: TurnContext,
        path: str,
        model_name: str,
        **kwargs,
    ) -> AsyncGenerator[str]:
        """Get a streaming OpenAI completion."""
        chat_completion: AsyncStream[ChatCompletionChunk] = await OpenaiCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            stream=True,
        )

        async def response_generator() -> AsyncGenerator[str]:
            async for chunk in chat_completion:
                if len(chunk.choices) == 0:
                    continue
                response = chunk.choices[0].delta.content
                if response is None:
                    continue
                yield response
                await asyncio.sleep(0)

        return response_generator()

    @staticmethod
    async def chat_completion(
        turn_context: TurnContext,
        path: str,
        model_name: str,
        stream: bool,
    ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
        """
        ### What
        - Fetch persisted messages from the database.
        - Convert the messages to the correct format.
        - Fetch completions from the OpenAI API using the messages as context.

        ### Why
        - The messages must be converted to the correct format to send them to the OpenAI API.
        - The context is needed to generate the completion.
        """
        persisted_messages: list[Message] = CompletionHandler.get_messages_by_conversation_id(
            conversation_id=turn_context.activity.conversation.id,
            bot_id=turn_context.activity.recipient.id,
        )
        system_message: Message = CompletionHandler.get_system_message(
            turn_context=turn_context,
            path=path,
        )
        if system_message is not None:
            persisted_messages.insert(0, system_message)
        chat_messages: list[ChatCompletionMessageParam] = [
            OpenaiCompletionHandler._message_to_chat_completion_message_param(message) for message in persisted_messages
        ]

        user_id = turn_context.activity.from_property.id or "UNKNOWN"
        user_email: str | None = None

        connector_client = turn_context.turn_state.get("ConnectorClient")

        if isinstance(connector_client, TeamsConnectorClient):
            teams_account: TeamsChannelAccount = await connector_client.get_conversation_member(
                turn_context.activity.conversation.id, user_id
            )
            if teams_account.email is not None:
                user_email = teams_account.email

        if not user_email:
            fallback = turn_context.activity.from_property.name
            if fallback and "@" in fallback:
                user_email = fallback
            else:
                raise ValueError(
                    f"Could not determine email for user '{turn_context.activity.from_property.name}'. "
                    "Ensure the user has logged in via OAuth2 before using the bot."
                )

        user_entity = UserEntity.by_email(user_email)
        tenant = AuthHandler.get_active_tenant_for_user(user_entity.id)
        user = UserIdentity.from_user_entity(user_entity, tenant)

        logger.debug(f"Using user identity: {user}")

        client: openai.AsyncClient = await LiteLLMService.openai_aclient_for_user(user=user)

        return await client.chat.completions.create(
            model=model_name,
            messages=chat_messages,
            stream=stream,
        )

    @staticmethod
    def _message_to_chat_completion_message_param(message: Message) -> ChatCompletionMessageParam:
        def remove_accents(input_str: str) -> str:
            # Normalize the string to decompose characters into base letters and diacritics
            normalized_str = unicodedata.normalize("NFKD", input_str)
            # Reconstruct string by ignoring diacritical marks
            return "".join([c for c in normalized_str if not unicodedata.combining(c)])

        def clean_name(_name: str) -> str:
            # OpenAI Regex: r"^[a-zA-Z0-9_-]+$"
            _name = remove_accents(_name)
            return re.sub("[^a-zA-Z0-9_-]", "_", _name)

        name = clean_name(message.name) or None

        match message.role:
            case "user":
                return ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        OpenaiCompletionHandler._content_to_chat_completion_content_param(content)
                        for content in message.content
                    ],
                    name=name,
                )
            case "bot":
                return ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=[
                        OpenaiCompletionHandler._content_to_chat_completion_content_param(content)
                        for content in message.content
                    ],
                    name=name,
                )
            case "system":
                return ChatCompletionSystemMessageParam(
                    role="system",
                    content=[
                        OpenaiCompletionHandler._content_to_chat_completion_content_param(content)
                        for content in message.content
                    ],
                    name=name,
                )
            case _:
                raise ValueError(f"Unsupported message role: {message.role}")

    @staticmethod
    def _content_to_chat_completion_content_param(content: Content) -> ChatCompletionContentPartParam:
        match content.type:
            case "text":
                return ChatCompletionContentPartTextParam(text=content.text, type="text")
            case "image_url":
                image_url: ImageURL = ImageURL(url=content.text, detail="auto")
                return ChatCompletionContentPartImageParam(image_url=image_url, type="image_url")
            case _:
                raise ValueError(f"Unsupported content type: {content.type}")

    @staticmethod
    @override
    async def handle_exception(
        turn_context: TurnContext,
        exception: Exception,
        typing_task: Task,
        typing_stop_signal: Event,
        t: LocaleHandler,
    ) -> str:
        if isinstance(exception, APIStatusError):
            logger.warning(f"APIStatusError: {exception}\nTurnContext: {turn_context}")
            typing_stop_signal.set()
            await typing_task
            if exception.body and isinstance(exception.body, dict) and "message" in exception.body:
                response = exception.body["message"]
            else:
                response = exception.message
            return response
        else:
            return await CompletionHandler.handle_exception(
                turn_context=turn_context,
                exception=exception,
                typing_task=typing_task,
                typing_stop_signal=typing_stop_signal,
                t=t,
            )
