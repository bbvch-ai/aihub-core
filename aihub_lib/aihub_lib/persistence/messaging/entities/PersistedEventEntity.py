from typing import List, TYPE_CHECKING

from bson import ObjectId
from llama_index.core.base.llms.types import MessageRole
from mongoengine import DictField, Document, StringField, ListField

from aihub_lib.nats.events.control import AssistantChatMessage, UserChatMessage
from aihub_lib.nats.topic_managers.TopicManager import TopicManager

if TYPE_CHECKING:
    from aihub_lib.nats.events import BaseEvent
    from aihub_lib.nats.topics import AgentTopic

class PersistedEventEntity(Document):
    meta = {
        "collection": "events",
        "strict": False,
    }
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    thread_id = StringField(required=True)
    display_id = StringField(required=True)
    run_id = StringField(required=True)
    event_id = StringField(required=True)
    event_type = StringField(required=True)
    event_name = StringField(required=True)
    event_data = DictField(required=True)
    event_parents = ListField(StringField(), required=True)

    @classmethod
    def persist_event(cls, event: "BaseEvent", topic: "AgentTopic", db: str):
        persisted_entity = cls(
            id=ObjectId(),
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            event_id=event.event_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_data=event.model_dump(),
            event_parents=event._parent_class_names
        )
        persisted_entity.switch_db(db)
        persisted_entity.save()

    @classmethod
    def display_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return (
            cls.objects()
            .filter(thread_id=thread_id, event_type=TopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    def display_events_for_threads(cls, thread_ids: List[str]) -> List["PersistedEventEntity"]:
        return (
            cls.objects()
            .filter(thread_id__in=thread_ids, event_type=TopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    def display_events_for_agent(cls, agent_id: str) -> List["PersistedEventEntity"]:
        return (
            cls.objects()
            .filter(agent_id=agent_id, event_type=TopicManager.DISPLAY_EVENT)
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_request_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return list(
            cls.objects()
            .filter(thread_id=thread_id, event_parents__contains="HumanInTheLoopRequestEvent")
            .order_by("event_data__created_at")
        )

    @classmethod
    def human_in_the_loop_response_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return list(
            cls.objects()
            .filter(
                thread_id=thread_id, event_parents__contains="HumanInTheLoopResponseEvent", event_type=TopicManager.CONTROL_EVENT
            )
            .order_by("event_data__created_at")
        )

    @classmethod
    def to_message_history(cls, thread_id: str) -> List[UserChatMessage | AssistantChatMessage]:
        # Retrieve and filter events from the database
        events = (
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_type=TopicManager.DISPLAY_EVENT,
                event_parents__in=[
                    "ChunkEvent",
                    "UserMessageEvent",
                    "HumanInTheLoopRequestEvent",
                    "HumanInTheLoopResponseEvent",
                ],
            )
            .order_by("event_data__created_at")
            .only("event_name", "event_data", "agent_id", "agent_class", "run_id")
        )

        message_history: List[UserChatMessage | AssistantChatMessage] = []
        assistant_content_buffer = ""
        current_run_id = None
        current_agent_id = None
        current_agent_class = None

        for event in events:
            if event.event_name in ["UserMessageEvent", "HumanInTheLoopResponseEvent"]:
                # Finalize any ongoing assistant message
                if assistant_content_buffer:
                    message_history.append(
                        AssistantChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=assistant_content_buffer,
                            agent_id=current_agent_id,
                            agent_class=current_agent_class,
                        )
                    )
                    assistant_content_buffer = ""
                    current_run_id = None
                    current_agent_id = None
                    current_agent_class = None

                # Create and append user message
                content = event.event_data.get("content", "") or event.event_data.get("response", "")
                message_history.append(
                    UserChatMessage(
                        role=MessageRole.USER,
                        content=content,
                        user_id=event.agent_id,
                    )
                )

            elif event.event_name in ["ChunkEvent", "HumanInTheLoopRequestEvent"]:
                # Check if we are continuing the same assistant message
                if current_run_id == event.run_id and current_agent_id == event.agent_id:
                    assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get(
                        "question", ""
                    )
                else:
                    # Finalize previous assistant message if it exists
                    if assistant_content_buffer:
                        message_history.append(
                            AssistantChatMessage(
                                role=MessageRole.ASSISTANT,
                                content=assistant_content_buffer,
                                agent_id=current_agent_id,
                                agent_class=current_agent_class,
                            )
                        )
                    # Start a new assistant message
                    assistant_content_buffer = event.event_data.get("content", "") or event.event_data.get(
                        "question", ""
                    )
                    current_run_id = event.run_id
                    current_agent_id = event.agent_id
                    current_agent_class = event.agent_class
            else:
                continue  # Skip other event types

        # Finalize any remaining assistant message
        if assistant_content_buffer:
            message_history.append(
                AssistantChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content_buffer,
                    agent_id=current_agent_id,
                    agent_class=current_agent_class,
                )
            )

        return message_history
