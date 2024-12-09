import logging
from datetime import timedelta

from nats.js.api import StorageType
from nats.js.client import JetStreamContext

from lib_core.nats.context.BaseContext import BaseContext

logger = logging.getLogger(__name__)


class ThreadContext(BaseContext):
    def __init__(self, js: JetStreamContext, thread_id: str):
        self.thread_id = thread_id
        store_name = f"thread_context_{thread_id}"
        logger.debug(f"Initializing ThreadContext with store name '{store_name}'")
        super().__init__(js, store_name)

    @classmethod
    async def create(cls, js: JetStreamContext, thread_id: str):
        # Create KV store with 30-day TTL if it doesn't exist
        try:
            await js.create_key_value(
                bucket=f"thread_context_{thread_id}",
                ttl=timedelta(days=30).seconds,
                history=1,
                storage=StorageType.FILE,
            )
            logger.debug(f"Created KV store 'thread_context_{thread_id}'")
        except Exception as e:
            if "already in use" in str(e).lower():
                # Bucket already exists, ignore
                logger.debug(f"KV store 'thread_context_{thread_id}' already in use")
                pass
            else:
                # Log the exception and re-raise
                logger.error(f"Error creating KV store 'thread_context_{thread_id}': {e}")
                raise e
        return cls(js, thread_id)
