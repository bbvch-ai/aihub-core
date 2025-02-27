import logging
from datetime import timedelta

from nats.js import JetStreamContext
from nats.js.api import KeyValueConfig, StorageType

from aihub_lib.nats.context.BaseContext import BaseContext

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

    def __init__(self, js: JetStreamContext, thread_id: str, run_id: str):
        self.thread_id = thread_id
        self.run_id = run_id
        store_name = f"run_context_{thread_id}_{run_id}"
        logger.debug(f"Initializing RunContext with store name '{store_name}'")
        super().__init__(js, store_name)

    @classmethod
    async def create(cls, js: JetStreamContext, thread_id: str, run_id: str):
        """
        Create a KV store for the run if it doesn't exist yet.

        Configurations:
        - TTL: 60 minutes to prevent stale data accumulation.
        - History: 1 version (only the latest value matters).
        - Storage: FILE for durability.

        If the store already exists, it's reused.
        """
        ttl_seconds = int(timedelta(minutes=60).total_seconds())
        try:
            await js.create_key_value(
                KeyValueConfig(
                    bucket=f"run_context_{thread_id}_{run_id}",
                    ttl=ttl_seconds,
                    history=1,
                    storage=StorageType.MEMORY,
                )
            )
            logger.debug(f"Created KV store 'run_context_{thread_id}_{run_id}' with TTL of {ttl_seconds} seconds")
        except Exception as e:
            if "already in use" in str(e).lower():
                logger.debug(f"KV store 'run_context_{thread_id}_{run_id}' already exists")
            else:
                logger.error(f"Error creating KV store 'run_context_{thread_id}_{run_id}': {e}")
                raise e
        return cls(js, thread_id, run_id)
