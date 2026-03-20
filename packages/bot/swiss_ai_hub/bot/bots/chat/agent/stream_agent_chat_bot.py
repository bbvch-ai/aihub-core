from typing import override

from microsoft_agents.activity import Channels
from microsoft_agents.hosting.core import TurnContext

from swiss_ai_hub.bot.bots.chat.agent.agent_chat_bot import AgentChatBot


class StreamAgentChatBot(AgentChatBot):
    @override
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.channel_id == Channels.webchat:
            return await super().on_message_activity(turn_context)

        await self._process_message(turn_context, is_streaming=True)
