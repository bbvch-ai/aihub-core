from typing import override

from microsoft_agents.hosting.core import TurnContext

from swiss_ai_hub.bot.bots.chat.openai.OpenaiChatBot import OpenaiChatBot


class StreamOpenaiChatBot(OpenaiChatBot):
    @override
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.channel_id == "webchat":
            return await super().on_message_activity(turn_context)

        await self._process_message(turn_context, is_streaming=True)
