import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.context import BaseContext

logger = logging.getLogger(__name__)


class WalkthroughContext(BaseContext):
    def __init__(self, redis: Redis, walkthrough_id: str):
        self.walkthrough_id = walkthrough_id
        store_name = f"walkthrough_context_{walkthrough_id}"
        logger.debug(f"Initializing WalkthroughContext with store name '{store_name}'")
        super().__init__(redis, store_name, default_ttl=60 * 60 * 24 * 30)  # 30 days in seconds
