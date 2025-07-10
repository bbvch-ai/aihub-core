import json
import logging
from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Generic type for value transformation


class StoreBase:
    """
    A base class for run-specific storage in Redis with race condition protection.

    ### Why StoreBase?
    In workflows, run-specific data (such as events, step counts, or other metadata) must be preserved
    between steps and even across server restarts. `StoreBase` provides a standardized way to manage
    these per-run key-value stores:
    - Creates a dedicated KV bucket for each run.
    - Ensures data has a reasonable TTL to avoid indefinite growth.
    - Simplifies cleanup at the end of a run.

    ### Key Concepts
    - **Per-Run Namespaces:** Each run gets its own Redis namespace (prefix:execution_context_id:key)
    - **TTL:** Keys have TTL to ensure stale data is eventually cleaned up
    - **Local Cache:** Redis connections are cached for reuse

    ### Lifecycle
    - At run start, when data is first stored for that run, a KV bucket is created if not existing.
    - During the run, data is written to this store.
    - At run end (StopEvent), `delete_run_store` removes the bucket, freeing up space.
    """

    def __init__(
        self,
        redis: Annotated[Redis, "Redis for KV storage"],
        prefix: Annotated[str, "Prefix for Redis keys"],
        default_ttl: Annotated[int, "How long redis stores keys in this store"] = 60
        * 60
        * 24
        * 30,  # 30 days in seconds
    ):
        self.redis = redis
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _build_key(self, run_id: str, key: str) -> str:
        """Build a namespaced Redis key"""
        return f"{self.prefix}:{run_id}:{key}"

    async def delete_all(self, run_id: str):
        """Deletes all keys for a specific run, removing all associated data."""
        try:
            pattern = f"{self.prefix}:{run_id}:*"
            scan_iter = self.redis.scan_iter(match=pattern, count=10_000)
            keys_to_delete = []

            async for key in scan_iter:
                keys_to_delete.append(key)

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                logger.debug(f"Deleted {len(keys_to_delete)} keys for run store '{self.prefix}_{run_id}'")
        except Exception as e:
            logger.exception(f"Error deleting run store '{self.prefix}_{run_id}': {e}")

    async def get_value(
        self, run_id: str, key: str, default_value: T = None, transform_func: Callable[[bytes], T] = None
    ) -> T:
        """Retrieves a value from the store, optionally transforming it."""
        redis_key = self._build_key(run_id, key)
        try:
            value = await self.redis.get(redis_key)
            if value is None:
                return default_value

            if transform_func:
                return transform_func(value)
            return value  # type: ignore
        except Exception as e:
            logger.exception(f"Error retrieving key '{redis_key}': {e}")
            return default_value

    async def get_json_value(self, run_id: str, key: str, default_value: Any = None) -> Any:
        """Retrieves and deserializes a JSON value from Redis."""

        def json_transform(value_bytes):
            return json.loads(value_bytes.decode())

        return await self.get_value(run_id, key, default_value, json_transform)

    async def put_value(self, run_id: str, key: str, value: bytes) -> bool:
        """Stores a raw byte value in Redis."""
        redis_key = self._build_key(run_id, key)
        try:
            await self.redis.set(redis_key, value, ex=self.default_ttl)
            return True
        except Exception as e:
            logger.exception(f"Error storing value for key '{redis_key}': {e}")
            return False

    async def put_json_value(self, run_id: str, key: str, value: Any) -> bool:
        """Stores a JSON-serializable value in Redis."""
        try:
            serialized = json.dumps(value).encode()
            return await self.put_value(run_id, key, serialized)
        except Exception as e:
            logger.exception(f"Error serializing JSON value for key '{key}': {e}")
            return False

    async def append_to_list(self, run_id: str, key: str, value: bytes) -> bool:
        """Appends a raw byte value to a Redis list."""
        redis_key = self._build_key(run_id, key)
        try:
            await self.redis.rpush(redis_key, value)
            await self.redis.expire(redis_key, self.default_ttl)
            return True
        except Exception as e:
            logger.exception(f"Error appending to list '{redis_key}': {e}")
            return False

    async def append_json_to_list(self, run_id: str, key: str, value: Any) -> bool:
        """Appends a JSON-serializable value to a Redis list."""
        try:
            serialized = json.dumps(value).encode()
            return await self.append_to_list(run_id, key, serialized)
        except Exception as e:
            logger.exception(f"Error serializing JSON value for list '{key}': {e}")
            return False

    async def get_list(self, run_id: str, key: str, transform_func: Callable[[bytes], T] = None) -> list[T]:
        """Retrieves all items from a Redis list with optional transformation."""
        redis_key = self._build_key(run_id, key)
        result = []
        try:
            values = await self.redis.lrange(redis_key, 0, -1)
            if not values:
                return result

            if transform_func:
                for value in values:
                    result.append(transform_func(value))
            else:
                result = values  # type: ignore

            return result
        except Exception as e:
            logger.exception(f"Error retrieving list '{redis_key}': {e}")
            return result

    async def increment_counter(self, run_id: str, key: str, amount: int = 1) -> int:
        """Increments a counter stored in Redis."""
        redis_key = self._build_key(run_id, key)
        try:
            count = await self.redis.incrby(redis_key, amount)
            await self.redis.expire(redis_key, self.default_ttl)
            return count
        except Exception as e:
            logger.exception(f"Error incrementing counter '{redis_key}': {e}")
            return 0
