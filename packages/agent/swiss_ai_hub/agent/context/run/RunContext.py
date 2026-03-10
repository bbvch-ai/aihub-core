import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.context.BaseContext import BaseContext
from swiss_ai_hub.core.nats.topics.agents.AgentClassTopic import AgentClassTopic

logger = logging.getLogger(__name__)


class RunContext(BaseContext):
    """
    A context dedicated to a single run within a thread, providing short-lived storage for ephemeral data.

    ### Why RunContext?
    While a thread might have long-lived state (e.g., user preferences or session info), individual runs within
    that thread often hold transient data that doesn't need to persist indefinitely. For example, intermediate
    steps or calculations within a run might only be relevant until the run completes or times out.

    By giving each run its own KV store (with a short TTL), RunContext:
    - Ensures data isolation between runs.
    - Reduces clutter by expiring run data after 60 minutes.
    - Simplifies cleanup, as outdated runs are automatically pruned.

    ### Use Cases
    - Storing intermediate state in complex multi-step workflows.
    - Temporary caching of retrieval results during a run.
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
