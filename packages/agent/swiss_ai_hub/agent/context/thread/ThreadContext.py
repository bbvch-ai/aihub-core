import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.context.BaseContext import BaseContext
from swiss_ai_hub.core.topics.agents.AgentClassTopic import AgentClassTopic

logger = logging.getLogger(__name__)


class ThreadContext(BaseContext):
    """
    A context for storing and retrieving thread-specific state information using a JetStream KV store.

    In multi-threaded or conversation-driven scenarios, you may want to persist state specific to a given
    thread (e.g., a conversation ID). This can include incremental results, user preferences, or session
    metadata that should outlive the runtime of any single agent step.

    Key Features are:
    - **Durable Storage:** Keys and values are persisted to a dedicated KV store, scoped by the thread_id.
    - **Time-to-Live (TTL):** The created KV store has a 30-day TTL, automatically expiring old entries and
      preventing unbounded growth.
    - **Isolated Namespaces:** Each thread_id maps to a unique KV store (bucket), ensuring minimal collisions
      and easy cleanup.
    """

    def __init__(self, redis: Redis, thread_id: str):
        self.thread_id = thread_id
        store_name = f"thread_context_{thread_id}"
        logger.debug(f"Initializing ThreadContext with store name '{store_name}'")
        super().__init__(redis, store_name, default_ttl=60 * 60 * 24 * 30)  # 30 days in seconds

    @classmethod
    def for_topic(cls, redis: Redis, topic: AgentClassTopic):
        return cls(redis, topic.thread_id)
