from typing import AsyncGenerator, List

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)

from aihub_bot.persistence.chat.entities.ConversationEntity import Message
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
    ) -> str:
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
    async def stream_on_message_completion(
        message: Message,
        conversation_id: str,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
    ) -> AsyncGenerator[str, None]:
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
                yield chunk.choices[0].delta.content

        return stream_chat_completion()
