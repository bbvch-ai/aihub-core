from swiss_ai_hub.core.events.agent import ConversationTitleEvent, DisplayEvent
from swiss_ai_hub.core.persistence import ThreadEntity
from swiss_ai_hub.core.topics import AgentInstanceTopic


class ThreadTitlePersister:
    """
    Durably ties a ConversationTitleEvent to ThreadEntity.name from a long-lived subscriber.

    Title persistence used to live in per-request display-event aggregators, which unsubscribe the
    moment the run's stop event is processed — a title emitted concurrently with the answer (e.g. the
    meta-question title step) could be dropped, permanently, because the producer-side once-per-thread
    flag is set on publish with no delivery acknowledgment. This handler runs on a subscriber
    registered once at API startup (a sibling of EventPersister and WebSocketSender) that never tears
    down mid-run, so delivery no longer races the request lifecycle.
    """

    @staticmethod
    async def persist_thread_title(event: DisplayEvent, topic: AgentInstanceTopic) -> None:
        """Persist the generated conversation title onto the thread; ignore every other display event."""
        if isinstance(event, ConversationTitleEvent):
            ThreadEntity.update_thread_name(topic.thread_id, event.title)
