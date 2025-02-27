import logging
from datetime import timedelta

from nats.js.api import StorageType
from nats.js.client import JetStreamContext

from aihub_lib.nats.context.BaseContext import BaseContext

logger = logging.getLogger(__name__)


class ThreadContext(BaseContext):
    """
    A context for storing and retrieving thread-specific state information using a JetStream KV store.

    ### Why ThreadContext?
    In multi-threaded or conversation-driven scenarios, you may want to persist state specific to a given
    thread (e.g., a conversation ID). This can include incremental results, user preferences, or session
    metadata that should outlive the runtime of any single agent step.

    ### Features
    - **Durable Storage:** Keys and values are persisted to a dedicated KV store, scoped by the thread_id.
    - **Time-to-Live (TTL):** The created KV store has a 30-day TTL, automatically expiring old entries and
      preventing unbounded growth.
    - **Isolated Namespaces:** Each thread_id maps to a unique KV store (bucket), ensuring minimal collisions
      and easy cleanup.

    ### Example
    An agent might store user preferences or intermediate conversation summaries in the ThreadContext so that
    if the system restarts or scales horizontally, state retrieval remains consistent across instances.

    """

    def __init__(self, js: JetStreamContext, thread_id: str):
        self.thread_id = thread_id
        store_name = f"thread_context_{thread_id}"
        logger.debug(f"Initializing ThreadContext with store name '{store_name}'")
        super().__init__(js, store_name)

    @classmethod
    async def create(cls, js: JetStreamContext, thread_id: str):
        """
        Create the KV store for the given thread_id if it doesn't already exist.

        The store uses:
        - A 30-day TTL to clean up old entries.
        - A single history version for simplicity.
        - File storage for durability.

        If the KV bucket already exists, this is a no-op.
        """
        ttl_seconds = int(timedelta(days=30).total_seconds())
        try:
            await js.create_key_value(
                bucket=f"thread_context_{thread_id}",
                ttl=ttl_seconds,
                history=1,
                storage=StorageType.MEMORY,
            )
            logger.debug(f"Created KV store 'thread_context_{thread_id}' with TTL of {ttl_seconds} seconds")
        except Exception as e:
            if "already in use" in str(e).lower():
                # Bucket already exists, just log and proceed
                logger.debug(f"KV store 'thread_context_{thread_id}' already exists")
            else:
                # Something else went wrong
                logger.error(f"Error creating KV store 'thread_context_{thread_id}': {e}")
                raise e
        return cls(js, thread_id)
