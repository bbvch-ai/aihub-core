import json
import logging
from typing import Annotated, Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class BaseContext:
    """
    A base class for managing state in a JetStream key-value (KV) store.

    ### Why This Class Exists
    Certain workflows or processes may need to persist runtime state, configuration, or intermediate results
    across restarts, between steps, or for debugging and auditing. BaseContext provides a simple API for
    reading, writing, and deleting key-value pairs in a JetStream-backed KV store. Derived classes (like
    ThreadContext or RunContext) add domain-specific behavior or naming conventions, but the core persistence
    logic lives here.

    ### Key Operations
    - **set**: Store a JSON-serializable object by key.
    - **get**: Retrieve and deserialize stored data, returning a default if not found or on error.
    - **delete**: Remove a specific key or the entire store.
    - **get_all**: Fetch all keys and values, useful for introspection or exporting state.
    - **to_json**: Serialize the entire store's data for logging, backup, or migration.

    ### Reliability
    By leveraging JetStream's KV store, BaseContext can rely on NATS for distributed durability and
    consistency, making the solution robust against failures and restarts.
    """

    def __init__(
        self,
        redis: Annotated[Redis, "Redis for KV storage"],
        store_name: Annotated[str, "Unique name under which all kv-pairs will be stored"],
        default_ttl: Annotated[int | None, "How long redis stores keys in this store, None for no expiry"] = None,
    ):
        self.redis = redis
        self.store_name = store_name
        self.default_ttl = default_ttl

    def _build_key(self, key: str) -> str:
        """Build a namespaced Redis key"""
        return f"{self.store_name}:{key}"

    async def set(self, key: str, value: Any):
        """
        Store a JSON-serializable value under the given key.
        Overwrites any existing value.
        """
        redis_key = self._build_key(key)
        serialized_value = json.dumps(value)
        logger.debug(f"Storing key '{redis_key}'")
        await self.redis.set(redis_key, serialized_value, ex=self.default_ttl)

    async def get(self, key: str, default: Any | None = None) -> Any | None:
        """
        Retrieve the value for `key`, returning `default` if not found or if there's an error.
        Deserializes the stored JSON string into a Python object.
        """
        redis_key = self._build_key(key)
        try:
            value = await self.redis.get(redis_key)
            if value is None:
                return default

            val = json.loads(value.decode())
            logger.debug(f"Retrieved key '{redis_key}'")
            return val
        except Exception as e:
            logger.exception(f"Error getting key '{redis_key}': {e}")
            return default

    async def delete(self, key: str):
        """Remove a specific key from the store, ignoring errors if the key doesn't exist."""
        redis_key = self._build_key(key)
        try:
            await self.redis.delete(redis_key)
            logger.debug(f"Deleted key '{redis_key}'")
        except Exception as e:
            logger.exception(f"Error deleting key '{redis_key}': {e}")

    async def delete_all(self):
        """
        Delete all keys with the store's prefix.
        """
        try:
            pattern = f"{self.store_name}:*"
            cursor = b"0"
            keys_to_delete = []

            while cursor:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=10_000)
                keys_to_delete.extend(keys)

                if cursor == b"0":
                    break

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                logger.debug(f"Deleted {len(keys_to_delete)} keys from store '{self.store_name}'")
        except Exception as e:
            logger.exception(f"Error deleting all keys for store '{self.store_name}': {e}")

        # No need to clear _redis as we can reuse the connection

    async def get_all(self) -> dict:
        """
        Fetch all key-value pairs currently stored.

        Returns a dictionary mapping keys to deserialized values. If a key is unreadable,
        logs the error and skips it.
        """
        try:
            pattern = f"{self.store_name}:*"
            cursor = b"0"
            keys = []

            while cursor:
                cursor, batch = await self.redis.scan(cursor=cursor, match=pattern, count=10_000)
                keys.extend(batch)

                if cursor == b"0":
                    break

            if not keys:
                return {}

            all_data = {}
            for key in keys:
                try:
                    value = await self.redis.get(key)
                    if value:
                        original_key = key.decode().split(":", 1)[1]
                        all_data[original_key] = json.loads(value.decode())
                except Exception as e:
                    logger.exception(f"Error retrieving value for key '{key.decode()}': {e}")
            return all_data
        except Exception as e:
            logger.exception(f"Error retrieving all keys for store '{self.store_name}': {e}")
            return {}

    async def to_serializable(self) -> dict:
        """
        Convert the entire context into a dictionary suitable for serialization.
        """
        return {
            "store_name": self.store_name,
            "data": await self.get_all(),
        }

    async def to_json(self) -> str:
        """
        Serialize the context's entire state into a JSON string.
        """
        serializable_data = await self.to_serializable()
        return json.dumps(serializable_data)
