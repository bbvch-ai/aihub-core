from typing import List, AsyncGenerator

from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import Activity, ResourceResponse
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS
from typing_extensions import override

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.chat.entities.ConversationEntity import Message, ConversationEntity
from aihub_bot.routes.chat.agent.AgentChatService import AgentChatService
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver


class StreamAgentChatBot(ChatBot):

    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        """
        A message activity is sent when a user sends a message to the bot.

        Persists user messages in the database and sends them to the AI agent for processing.
        Sends the message history to the agent for context.
        The agent's response is also persisted in the database and sent back to the user.

        The agent's response is streamed back to the user by updating the message activity with each response chunk.
        """
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role,
        )
        AgentChatService.add_message_to_conversation(turn_context.activity.conversation.id, user_message)
        persisted_messages: List[Message] = AgentChatService.get_messages_by_conversation_id(
            turn_context.activity.conversation.id
        )
        messages: List[ChatMessage] = [AgentChatService.message_to_chat_message(message) for message in
                                       persisted_messages]
        response_generator: AsyncGenerator[str, None] = await AgentChatService.stream_chat(
            user_id=turn_context.activity.from_property.id,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            messages=messages,
            nc=self.nc,
            ws_receiver=self.ws_receiver,
        )
        # Send a message activity for the first response
        try:
            response: str = await response_generator.__anext__()
        except StopAsyncIteration:
            response = "No response from the agent."
        message: ResourceResponse = await turn_context.send_activity(response)

        # Update the message with the rest of the responses
        async for chunk in response_generator:
            response = response + chunk
            activity: Activity = MessageFactory.text(response)
            activity.id = message.id
            await turn_context.update_activity(activity)

        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=response,
            role=turn_context.activity.recipient.role,
        )
        ConversationEntity.add_message_to_conversation(turn_context.activity.conversation.id, bot_message)
