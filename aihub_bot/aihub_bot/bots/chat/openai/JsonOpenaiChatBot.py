from typing_extensions import override

from botbuilder.core import TurnContext
from openai import AsyncAzureOpenAI, AsyncOpenAI

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.chat.entities.ConversationEntity import Message
from aihub_bot.routes.chat.openai.OpenaiChatService import OpenaiChatService


class JsonOpenaiChatBot(ChatBot):
    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
    ):
        self.model_name = model_name
        self.client = client

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role or "user",
        )
        response = await OpenaiChatService.json_on_message_activity(
            message=user_message,
            conversation_id=turn_context.activity.conversation.id,
            model_name=self.model_name,
            client=self.client,
        )
        return await OpenaiChatService.respond_to_user(
            turn_context,
            turn_context.activity,
            response,
        )
