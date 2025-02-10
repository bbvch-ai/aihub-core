from typing import AsyncGenerator

from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import Activity
from openai import AsyncAzureOpenAI, AsyncOpenAI
from typing_extensions import override

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.chat.entities.ConversationEntity import Message
from aihub_bot.routes.chat.openai.OpenaiChatService import OpenaiChatService


class StreamOpenaiChatBot(ChatBot):
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
        response_generator: AsyncGenerator[str, None] = await OpenaiChatService.stream_on_message_completion(
            message=user_message,
            conversation_id=turn_context.activity.conversation.id,
            model_name=self.model_name,
            client=self.client,
        )
        response: str
        try:
            response = await response_generator.__anext__()
        except StopAsyncIteration:
            response = "No response from the agent."
        message = await turn_context.send_activity(response)

        async for chunk in response_generator:
            if chunk is None:
                break
            response = response + chunk
            activity: Activity = MessageFactory.text(response)
            activity.id = message.id
            await turn_context.update_activity(activity)

        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=response,
            role=turn_context.activity.recipient.role or "bot",
        )
        OpenaiChatService.add_message_to_conversation(turn_context.activity.conversation.id, bot_message)
