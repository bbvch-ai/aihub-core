from botbuilder.core import TurnContext
from botbuilder.schema import Activity
from openai import AsyncAzureOpenAI, AsyncOpenAI
from typing_extensions import override

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.entities.ConversationEntity import Message
from aihub_bot.routes.chat.openai.OpenaiChatService import OpenaiChatService


class JsonOpenaiChatBot(ChatBot):
    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        path: str,
    ):
        self.model_name = model_name
        self.client = client
        self.path = path

    @override
    async def on_turn(self, turn_context: TurnContext):
        return await super().on_turn(turn_context)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role or "user",
        )
        is_slack: bool = turn_context.activity.channel_id == "slack"

        username = turn_context.activity.from_property.name
        response = await OpenaiChatService.json_on_message_activity(
            message=user_message,
            conversation_id=turn_context.activity.conversation.id,
            model_name=self.model_name,
            client=self.client,
            path=self.path,
            username=username,
        )
        bot_activity: Activity = Activity()

        if is_slack:
            channel_data = turn_context.activity.channel_data
            ts: str = channel_data["SlackMessage"]["event"]["ts"]
            bot_activity.channel_data = {"thread_ts": ts, "text": response}

        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=response,
            role=turn_context.activity.recipient.role or "bot",
        )
        OpenaiChatService.add_message_to_conversation(turn_context.activity.conversation.id, bot_message)
        return await turn_context.send_activity(bot_activity)
