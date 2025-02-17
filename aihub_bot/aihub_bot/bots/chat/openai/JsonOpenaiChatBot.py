import re
from typing import Optional

from botbuilder.core import TurnContext
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
        is_slack: bool = turn_context.activity.channel_id == "slack"
        slack_parent_conversation_id: Optional[str] = None
        if is_slack:
            coversation_id: str = turn_context.activity.conversation.id
            channel_id_regex = re.compile(r"^B[0-9A-Z]{10}:T[0-9A-Z]{10}:C[0-9A-Z]{10}$")
            if channel_id_regex.match(coversation_id):
                channel_data = turn_context.activity.channel_data
                ts: str = channel_data["SlackMessage"]["event"]["ts"]
                turn_context.activity.conversation.id = coversation_id + f":{ts}"
                slack_parent_conversation_id = coversation_id

        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role or "user",
        )
        username = turn_context.activity.from_property.name
        response = await OpenaiChatService.json_on_message_activity(
            message=user_message,
            conversation_id=turn_context.activity.conversation.id,
            model_name=self.model_name,
            client=self.client,
            path=self.path,
            username=username,
            parent_conversation_id=slack_parent_conversation_id,
        )
        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=response,
            role=turn_context.activity.recipient.role or "bot",
        )
        OpenaiChatService.add_message_to_conversation(turn_context.activity.conversation.id, bot_message)
        return await turn_context.send_activity(response)
