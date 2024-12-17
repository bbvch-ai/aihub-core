from typing import List

from llama_index.core.base.llms.types import MessageRole
from mongoengine import Document, StringField, DictField

from lib_core.nats.events.control import UserChatMessage, AssistantChatMessage
from lib_core.nats.topic_managers.TopicManager import TopicManager


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

    @classmethod
    def display_events_for_thread(cls, thread_id: str) -> List["PersistedEventEntity"]:
        return cls.objects().filter(thread_id=thread_id, event_type=TopicManager.DISPLAY_EVENT)

    @classmethod
    def display_events_for_threads(cls, thread_ids: List[str]) -> List["PersistedEventEntity"]:
        return cls.objects().filter(thread_id__in=thread_ids, event_type=TopicManager.DISPLAY_EVENT)

    @classmethod
    def display_events_for_agent(cls, agent_id: str) -> List["PersistedEventEntity"]:
        return cls.objects().filter(agent_id=agent_id, event_type=TopicManager.DISPLAY_EVENT)

    @classmethod
    def to_message_history(cls, thread_id: str) -> List[UserChatMessage | AssistantChatMessage]:
        # Retrieve and filter events from the database
        events = (
            cls.objects()
            .filter(
                thread_id=thread_id,
                event_type=TopicManager.DISPLAY_EVENT,
                event_name__in=["ChunkEvent", "UserMessageEvent"],
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
            if event.event_name == "UserMessageEvent":
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
                content = event.event_data.get("content", "")
                message_history.append(
                    UserChatMessage(
                        role=MessageRole.USER,
                        content=content,
                        user_id=event.agent_id,
                    )
                )

            elif event.event_name == "ChunkEvent":
                # Check if we are continuing the same assistant message
                if current_run_id == event.run_id and current_agent_id == event.agent_id:
                    assistant_content_buffer += event.event_data.get("content", "")
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
                    assistant_content_buffer = event.event_data.get("content", "")
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
