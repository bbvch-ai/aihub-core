import asyncio
from typing import AsyncGenerator, List

from botbuilder.core import TurnContext
from openai import AsyncAzureOpenAI, AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartImageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL

from aihub_bot.persistence.entities.ConversationEntity import Message, Content
from aihub_bot.routes.Service import Service
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig


class OpenaiChatService(Service):
    """
    ### What
    - Shared functionality for the OpenaiChatController and OpenaiChatBots.
    """

    @staticmethod
    def get_client(
        models: List[ChatLLMConfig],
        model_name: str,
    ) -> AsyncOpenAI | AsyncAzureOpenAI:
        """
        ### What
        - Get the asynchronous `OpenAI` client for the specified model.

        ### Why
        - The client is needed to fetch completions from the OpenAI API.
        """
        matches = [model for model in models if model.name == model_name]
        if len(matches) == 0:
            raise ValueError(f"Model {model_name} not found.")
        model_config = matches[0]
        llm, _ = model_config.to_llama_index()
        return llm._get_aclient()

    @staticmethod
    async def json_chat_completion(
        turn_context: TurnContext,
        path: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        model_name: str,
    ) -> str:
        """
        ### What
        - Fetch a single completion from the OpenAI API.

        ### Why
        - Send the response in one single message.
        - Some channels (e.g. webchat) do not support streaming.
        """
        chat_completion: ChatCompletion = await OpenaiChatService.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            client=client,
            stream=False,
        )
        return chat_completion.choices[0].message.content

    @staticmethod
    async def stream_chat_completion(
        turn_context: TurnContext,
        path: str,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
    ) -> AsyncGenerator[str, None]:
        """
        ### What
        - Fetch completions from the OpenAI API in a stream.
        - Return a generator that yields the response in chunks.

        ### Why
        - Send the response in multiple chunks by updating the message for each chunk.
        """
        chat_completion: AsyncStream[ChatCompletionChunk] = await OpenaiChatService.chat_completion(
            turn_context=turn_context,
            path=path,
            model_name=model_name,
            client=client,
            stream=True,
        )

        async def response_generator() -> AsyncGenerator[str, None]:
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
        client: AsyncOpenAI | AsyncAzureOpenAI,
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
        persisted_messages: List[Message] = Service.get_messages_by_conversation_id(
            conversation_id=turn_context.activity.conversation.id
        )
        system_message: Message = Service.get_system_message(
            turn_context=turn_context,
            path=path,
        )
        if system_message is not None:
            persisted_messages.insert(0, system_message)
        chat_messages: List[ChatCompletionMessageParam] = [
            OpenaiChatService._message_to_chat_completion_message_param(message) for message in persisted_messages
        ]
        return await client.chat.completions.create(
            model=model_name,
            messages=chat_messages,
            stream=stream,
        )

    @staticmethod
    def _message_to_chat_completion_message_param(message: Message) -> ChatCompletionMessageParam:
        match message.role:
            case "user":
                return ChatCompletionUserMessageParam(
                    role="user",
                    content=[ChatCompletionContentPartTextParam(text=message.content, type="text")],
                )
            case "bot":
                return ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=[ChatCompletionContentPartTextParam(text=message.content, type="text")],
                )
            case "system":
                return ChatCompletionSystemMessageParam(
                    role="system", content=[ChatCompletionContentPartTextParam(text=message.content, type="text")]
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
