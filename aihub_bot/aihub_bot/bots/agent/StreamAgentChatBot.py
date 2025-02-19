from typing import AsyncGenerator

from botbuilder.core import TurnContext
from typing_extensions import override

from aihub_bot.bots.agent.AgentChatBot import AgentChatBot
from aihub_bot.routes.agent.AgentChatService import AgentChatService


class StreamAgentChatBot(AgentChatBot):
    """
    See `AgentChatBot` for more information.

    ### What
    - Responds with an initial `Activity`, which is then asynchronously updated with the Agent's responses.

    ### Why
    - Compared to the `AgentChatBot`, the user can see the Agent's response as it is being generated.
    """

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.channel_id == "webchat":
            return await super().on_message_activity(turn_context)

        AgentChatService.add_user_message_to_conversation(turn_context)

        if turn_context.activity.channel_id == "slack" and AgentChatService.is_slack_channel_message(turn_context):
            if not AgentChatService.is_bot_mentioned(turn_context):
                return
            turn_context = AgentChatService.update_slack_turn_context(turn_context)

        AgentChatService.get_system_message(
            turn_context=turn_context,
            path=self.path,
        )

        response_generator: AsyncGenerator[str, None] = await AgentChatService.stream_chat_completion(
            turn_context=turn_context,
            path=self.path,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            nc=self.nc,
            ws_receiver=self.ws_receiver,
        )

        response = await AgentChatService.send_response_stream(
            turn_context=turn_context,
            response_generator=response_generator,
        )

        AgentChatService.add_bot_message_to_conversation(
            turn_context=turn_context,
            message=response,
        )
