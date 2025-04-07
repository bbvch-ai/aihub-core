from botbuilder.core import TurnContext
from typing_extensions import override

from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot


class StreamAgentChatBot(AgentChatBot):
    @override
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.channel_id == "webchat":
            return await super().on_message_activity(turn_context)

        await self._process_message(turn_context, is_streaming=True)
