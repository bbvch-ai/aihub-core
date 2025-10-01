import asyncio
import logging
import re

import openai
import unicodedata
from asyncio import Event, Task
from collections.abc import AsyncGenerator
from typing import override

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from microsoft_agents.hosting.core import TurnContext
from openai import APIStatusError, AsyncAzureOpenAI, AsyncOpenAI, AsyncStream
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

from aihub_bot.bots.chat.CompletionHandler import CompletionHandler
from aihub_bot.persistence.entities.ConversationEntity import Content, Message

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
        client: openai.AsyncClient,
        **kwargs,
    ) -> str:
        chat_completion: ChatCompletion = await OpenaiCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            client=client,
            stream=False,
        )
        return chat_completion.choices[0].message.content

    @staticmethod
    async def get_stream_completion(
        turn_context: TurnContext,
        path: str,
        model_name: str,
        client: openai.AsyncClient,
        **kwargs,
    ) -> AsyncGenerator[str]:
        """Get a streaming OpenAI completion."""
        chat_completion: AsyncStream[ChatCompletionChunk] = await OpenaiCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            client=client,
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
        client: openai.AsyncClient,
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
            conversation_id=turn_context.activity.conversation.id
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
            return await super().handle_exception(
                turn_context=turn_context,
                exception=exception,
                typing_task=typing_task,
                typing_stop_signal=typing_stop_signal,
                t=t,
            )
