import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.context import BaseContext
from swiss_ai_hub.core.topics.agents.agent_class_topic import AgentClassTopic

logger = logging.getLogger(__name__)


class RunContext(BaseContext):
    """
    Per-run state in Valkey with a 30-day TTL safety net.

    Cleaned up explicitly on StopEvent. The TTL only catches orphaned runs from crashes.
    This data cannot be reconstructed from events — it holds intermediate computation
    results (hop counts, accumulated queries, etc.) that only exist here.
    """

    def __init__(self, redis: Redis, thread_id: str, run_id: str):
        self.thread_id = thread_id
        self.run_id = run_id
        store_name = f"run_context_{thread_id}_{run_id}"
        logger.debug(f"Initializing RunContext with store name '{store_name}'")
        super().__init__(redis, store_name, default_ttl=60 * 60 * 24 * 30)  # 30 days in seconds

    @classmethod
    def for_topic(cls, redis: Redis, topic: AgentClassTopic):
        return cls(redis, topic.thread_id, topic.run_id)
