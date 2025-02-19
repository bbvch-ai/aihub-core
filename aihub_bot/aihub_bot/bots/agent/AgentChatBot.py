from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from botbuilder.core import ActivityHandler, TurnContext
from nats.aio.client import Client as NATS
from typing_extensions import override

from aihub_bot.routes.agent.AgentChatService import AgentChatService


class AgentChatBot(ActivityHandler):
    """
    ### What
    - Handle incoming chat messages directed at an Agent defined by `agent_class` and `agent_id`.
    - Responds with a single `Activity` containing the answer of the Agent.

    ### Why
    - The Agent can be reached over multiple channels (e.g. Slack, Teams, ...).
    - Compared to the `OpenaiChatBot`, Agents can have advanced functionality (e.g. RAG).
    """

    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str, path: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.path = path

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        AgentChatService.add_user_message_to_conversation(turn_context)

        if turn_context.activity.channel_id == "slack" and AgentChatService.is_slack_channel_message(turn_context):
            if not AgentChatService.is_bot_mentioned(turn_context):
                return
            turn_context = AgentChatService.update_slack_turn_context(turn_context)

        response = await AgentChatService.json_chat_completion(
            turn_context=turn_context,
            path=self.path,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            nc=self.nc,
            ws_receiver=self.ws_receiver,
        )

        AgentChatService.add_bot_message_to_conversation(
            turn_context=turn_context,
            message=response,
        )

        return await turn_context.send_activity(response)
