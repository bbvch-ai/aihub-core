import asyncio
from asyncio import Event, Task
from typing import AsyncGenerator

from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
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

        typing_stop_signal = Event()
        typing: Task = asyncio.create_task(
            AgentChatService.send_typing_activity(
                turn_context=turn_context,
                signal=typing_stop_signal,
            )
        )
        AgentChatService.add_user_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
        )

        if turn_context.activity.channel_id == "slack":
            turn_context = AgentChatService.handle_slack_message(turn_context)
            if turn_context is None:
                return

        response_generator: AsyncGenerator[str, None] = await AgentChatService.stream_chat_completion(
            turn_context=turn_context,
            path=self.path,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            nc=self.nc,
            external_event_distributor=self.external_event_distributor,
            thread_id=ThreadEntity.to_thread_id(turn_context.activity.conversation.id),
        )

        typing_stop_signal.set()
        await typing
        response = await AgentChatService.send_response_stream(
            turn_context=turn_context,
            response_generator=response_generator,
        )

        AgentChatService.add_bot_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
            message=response,
        )
