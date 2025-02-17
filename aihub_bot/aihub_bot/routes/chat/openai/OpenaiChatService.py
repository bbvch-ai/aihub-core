import asyncio
from typing import AsyncGenerator, List, Optional

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
)

from aihub_bot.persistence.entities.ConversationEntity import Message
from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig


class OpenaiChatService(ChatService):
    @staticmethod
    def message_to_chat_completion_message_param(message: Message) -> ChatCompletionMessageParam:
        if message.role == "user":
            return ChatCompletionUserMessageParam(
                role="user",
                content=message.content,
            )
        if message.role == "bot":
            return ChatCompletionAssistantMessageParam(
                role="assistant",
                content=message.content,
            )
        if message.role == "system":
            return ChatCompletionSystemMessageParam(
                role="system",
                content=message.content,
            )

        raise ValueError(f"Unsupported message role: {message.role}")

    @staticmethod
    def get_client(
        models: List[ChatLLMConfig],
        model_name: str,
    ) -> AsyncOpenAI | AsyncAzureOpenAI:
        matches = [model for model in models if model.name == model_name]
        if len(matches) == 0:
            raise ValueError(f"Model {model_name} not found.")
        model_config = matches[0]
        llm, _ = model_config.to_llama_index()
        return llm._get_aclient()

    @staticmethod
    async def json_on_message_activity(
        message: Message,
        conversation_id: str,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        path: str,
        username: str,
        parent_conversation_id: Optional[str] = None,
    ) -> str:
        if parent_conversation_id is not None:
            parent_messages: List[Message] = OpenaiChatService.get_messages_by_conversation_id(parent_conversation_id)
            OpenaiChatService.create_conversation_if_not_exists(conversation_id, parent_messages)
            OpenaiChatService.add_message_to_conversation(parent_conversation_id, message)
        OpenaiChatService.add_system_message_to_conversation(conversation_id, path, username)
        OpenaiChatService.add_message_to_conversation(conversation_id, message)
        persisted_messages: List[Message] = OpenaiChatService.get_messages_by_conversation_id(conversation_id)
        messages: List[ChatCompletionMessageParam] = [
            OpenaiChatService.message_to_chat_completion_message_param(message) for message in persisted_messages
        ]
        chat_completion: ChatCompletion = await client.chat.completions.create(
            model=model_name, messages=messages, stream=False
        )
        return chat_completion.choices[0].message.content

    @staticmethod
    async def stream_on_message_activity(
        message: Message,
        conversation_id: str,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        path: str,
        username: str,
    ) -> AsyncGenerator[str, None]:
        OpenaiChatService.add_system_message_to_conversation(conversation_id, path, username)
        OpenaiChatService.add_message_to_conversation(conversation_id, message)
        persisted_messages: List[Message] = OpenaiChatService.get_messages_by_conversation_id(conversation_id)
        messages: List[ChatCompletionMessageParam] = [
            OpenaiChatService.message_to_chat_completion_message_param(message) for message in persisted_messages
        ]

        async def stream_chat_completion() -> AsyncGenerator[str, None]:
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
            )
            async for chunk in response:
                if len(chunk.choices) == 0:
                    continue
                content = chunk.choices[0].delta.content
                if content is None:
                    continue
                yield content
                await asyncio.sleep(0)

        return stream_chat_completion()
