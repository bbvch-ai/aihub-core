import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.context import BaseContext
from swiss_ai_hub.core.topics.agents.agent_class_topic import AgentClassTopic

logger = logging.getLogger(__name__)


class ThreadContext(BaseContext):
    """
    Durable per-thread state in Valkey, persisted across runs with no TTL.

    This data cannot be reconstructed from events — it holds arbitrary agent-set state
    (user preferences, namespace selections, accumulated context) that only exists here.
    """

    def __init__(self, redis: Redis, thread_id: str):
        self.thread_id = thread_id
        store_name = f"thread_context_{thread_id}"
        logger.debug(f"Initializing ThreadContext with store name '{store_name}'")
        super().__init__(redis, store_name)

    @classmethod
    def for_topic(cls, redis: Redis, topic: AgentClassTopic):
        return cls(redis, topic.thread_id)
