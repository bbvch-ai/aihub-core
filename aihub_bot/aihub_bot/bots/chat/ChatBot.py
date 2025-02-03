import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_lib.generative_ai.llms.costs.LLMCosts import LLMCosts
from aihub_lib.nats.events import UserMessageEvent, ChunkEvent, DisplayEvent, StopEvent, LLMCostEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics import AgentTopic
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity, Agent, User
from aihub_lib.sockets.events.user_to_server.WSUserEvent import WSUserEvent
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver

logger = logging.getLogger(__name__)


@dataclass
class JsonResources:
    """
    Holds resources for JSON-based responses:
    - stop_event: Signals when the run is complete.
    - subscriber: Subscribed to display events.
    - chunk_events: Accumulated chunk events for constructing the final response.
    - costs: Tracks LLMCostEvents for usage reporting.
    - model_name: Tracks the LLM model name used.
    """

    stop_event: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: List[ChunkEvent]
    costs: LLMCosts
    model_name: str


class ChatBot(ActivityHandler):
    messages: Dict[str, List[ChatMessage]] = {}
    users: Dict[str, str] = {}

    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

    @staticmethod
    def _save_user(from_property_id: str):
        ChatBot.users[from_property_id] = str(ObjectId())

    @staticmethod
    def _get_user_id(from_property_id: str) -> str:
        if from_property_id not in ChatBot.users:
            ChatBot._save_user(from_property_id)
        return ChatBot.users[from_property_id]

    @staticmethod
    def _save_chat_message(conversation_id: str, text: str):
        if conversation_id not in ChatBot.messages:
            ChatBot.messages[conversation_id] = []
        ChatBot.messages[conversation_id].append(ChatMessage(content=text))

    @staticmethod
    def _get_chat_messages(conversation_id: str) -> List[ChatMessage]:
        if conversation_id in ChatBot.messages:
            return ChatBot.messages[conversation_id]
        return []

    async def _start_json_chat_interaction(
            self,
        user_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> JsonResources:
        thread = ThreadEntity.create_thread(
            name="chat",
            users=[User(user_id=user_id)],
            agents=[Agent(agent_class=self.agent_class, agent_id=self.agent_id)],
        )
        logger.debug(f"Created thread: {thread.id}")

        event = WSUserEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=UserMessageEvent(
                messages=messages[:-1],
                content=messages[-1].content,
            ),
        )
        logger.debug(f"Created event: {event}")

        topic_manager = AgentThreadTopicManager(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )

        stop_event = asyncio.Event()
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        model_name = "bbv-ai-hub"

        resources = JsonResources(
            stop_event=stop_event,
            subscriber=None,  # assigned after subscriber creation
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name,
        )

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                resources.chunk_events.append(display_event)
            elif isinstance(display_event, StopEvent):
                logger.debug("Received stop event. Stop streaming")
                await resources.subscriber.stop()
                resources.stop_event.set()
            elif isinstance(display_event, LLMCostEvent):
                resources.costs += display_event
                resources.model_name = display_event.llm_name

        subscriber = NCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )
        resources.subscriber = subscriber

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction
        await ws_receiver.receive_event(event, user_id)
        return resources

    @staticmethod
    def _build_json_response(chunk_events: List[ChunkEvent], costs: LLMCosts, model_name: str) -> str:
        chunk_events = sorted(chunk_events, key=lambda x: x.created_at)
        content = "".join([chunk.content for chunk in chunk_events])
        return content

    async def _json_chat(
        self,
        user_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> str:
        resources: JsonResources = await self._start_json_chat_interaction(user_id, messages, nc, ws_receiver)

        # Wait until all events are processed
        await resources.stop_event.wait()
        await resources.subscriber.stop()

        # Construct final JSON response
        return ChatBot._build_json_response(resources.chunk_events, resources.costs, resources.model_name)

    async def on_members_added_activity(self, members_added: [ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                self._save_user(turn_context.activity.from_property.id)
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        activity: Activity = turn_context.activity
        self._save_chat_message(activity.conversation.id, activity.text)
        messages: List[ChatMessage] = self._get_chat_messages(activity.conversation.id)
        user_id: str = self._get_user_id(activity.from_property.id)
        response: str = await self._json_chat(user_id, messages, self.nc, self.ws_receiver)
        return await turn_context.send_activity(response)
