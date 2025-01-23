import json
import logging
from typing import Any, Optional

from nats.js.client import JetStreamContext

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
    - **to_json**: Serialize the entire store’s data for logging, backup, or migration.

    ### Reliability
    By leveraging JetStream’s KV store, BaseContext can rely on NATS for distributed durability and
    consistency, making the solution robust against failures and restarts.
    """

    def __init__(self, js: JetStreamContext, store_name: str):
        self.js = js
        self.store_name = store_name
        self._kv = None

    async def _ensure_kv_store(self):
        """
        Lazily fetches the KV store reference from JetStream.
        This avoids initializing the store prematurely and handles missing stores gracefully.
        """
        if self._kv is None:
            self._kv = await self.js.key_value(self.store_name)

    async def set(self, key: str, value: Any):
        """
        Store a JSON-serializable value under the given key.
        Overwrites any existing value.
        """
        await self._ensure_kv_store()
        serialized_value = json.dumps(value)
        logger.debug(f"Storing key '{key}' with value: {serialized_value}")
        await self._kv.put(key, serialized_value.encode())

    async def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieve the value for `key`, returning `default` if not found or if there's an error.
        Deserializes the stored JSON string into a Python object.
        """
        await self._ensure_kv_store()
        try:
            entry = await self._kv.get(key)
            val = json.loads(entry.value.decode())
            logger.debug(f"Retrieved key '{key}' with value: {val}")
            return val
        except Exception as e:
            logger.error(f"Error getting key '{key}': {e}")
            return default

    async def delete(self, key: str):
        """Remove a specific key from the store, ignoring errors if the key doesn't exist."""
        await self._ensure_kv_store()
        try:
            await self._kv.delete(key)
            logger.debug(f"Deleted key '{key}'")
        except Exception as e:
            logger.error(f"Error deleting key '{key}': {e}")

    async def delete_all(self):
        """
        Delete the entire KV bucket.
        After this, the internal `_kv` reference is cleared, requiring a fresh initialization if needed again.
        """
        await self.js.delete_key_value(self.store_name)
        logger.debug(f"Deleted entire store '{self.store_name}'")
        self._kv = None

    async def get_all(self) -> dict:
        """
        Fetch all key-value pairs currently stored.

        Returns a dictionary mapping keys to deserialized values. If a key is unreadable,
        logs the error and skips it.
        """
        await self._ensure_kv_store()
        try:
            keys = await self._kv.keys()
            if not keys:
                return {}

            all_data = {}
            for key in keys:
                try:
                    entry = await self._kv.get(key)
                    value = json.loads(entry.value.decode())
                    all_data[key] = value
                except Exception as e:
                    logger.error(f"Error retrieving value for key '{key}': {e}")
            return all_data
        except Exception as e:
            logger.error(f"Error retrieving all keys: {e}")
            return {}

    async def to_serializable(self) -> dict:
        """
        Convert the entire context (store name and all key-value data) into a dictionary suitable for serialization.
        Useful for exporting state or debugging.
        """
        return {
            "store_name": self.store_name,
            "data": await self.get_all(),
        }

    async def to_json(self) -> str:
        """
        Serialize the context's entire state (including all keys and values) into a JSON string.
        This can be used for logging, backups, or transferring context state between systems.
        """
        serializable_data = await self.to_serializable()
        return json.dumps(serializable_data)
