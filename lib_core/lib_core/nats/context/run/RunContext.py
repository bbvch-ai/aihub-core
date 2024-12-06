import logging
from datetime import timedelta

from nats.js import JetStreamContext
from nats.js.api import StorageType, KeyValueConfig

from lib_core.nats.context.BaseContext import BaseContext

logger = logging.getLogger(__name__)


class RunContext(BaseContext):
    def __init__(self, js: JetStreamContext, thread_id: str, run_id: str):
        self.thread_id = thread_id
        self.run_id = run_id
        store_name = f"run_context_{thread_id}_{run_id}"
        logger.debug(f"Initializing RunContext with store name '{store_name}'")
        super().__init__(js, store_name)

    @classmethod
    async def create(cls, js: JetStreamContext, thread_id: str, run_id: str):
        # Create KV store with 60-minute TTL if it doesn't exist
        try:
            await js.create_key_value(
                KeyValueConfig(
                    bucket=f"run_context_{thread_id}_{run_id}",
                    ttl=timedelta(minutes=60).seconds,
                    history=1,
                    storage=StorageType.FILE
                )
            )
            logger.debug(f"Created KV store 'run_context_{thread_id}_{run_id}'")
        except Exception as e:
            if 'already in use' in str(e).lower():
                # Bucket already exists, ignore
                logger.debug(f"KV store 'run_context_{thread_id}_{run_id}' already in use")
                pass
            else:
                # Log the exception and re-raise
                logger.error(f"Error creating KV store 'run_context_{thread_id}_{run_id}': {e}")
                raise e
        return cls(js, thread_id, run_id)
