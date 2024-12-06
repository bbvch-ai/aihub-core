import logging
from typing import Any, Optional
import json
from nats.js.client import JetStreamContext

logger = logging.getLogger(__name__)


class BaseContext:
    def __init__(self, js: JetStreamContext, store_name: str):
        self.js = js
        self.store_name = store_name
        self._kv = None

    async def _ensure_kv_store(self):
        if self._kv is None:
            self._kv = await self.js.key_value(self.store_name)

    async def set(self, key: str, value: Any):
        await self._ensure_kv_store()
        serialized_value = json.dumps(value)
        logger.debug(f"Serialized value for {key}: {serialized_value}")
        await self._kv.put(key, serialized_value.encode())

    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_kv_store()
        try:
            entry = await self._kv.get(key)
            val = json.loads(entry.value.decode())
            logger.debug(f"Deserialized value for {key}: {val}")
            return val
        except Exception as e:
            logger.error(f"Error getting key '{key}': {e}")
            return None

    async def delete(self, key: str):
        await self._ensure_kv_store()
        try:
            await self._kv.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key '{key}': {e}")
            pass

    async def delete_all(self):
        # Delete the entire KV store (bucket)
        await self.js.delete_key_value(self.store_name)
        self._kv = None

    async def get_all(self) -> dict:
        """Retrieve all key-value pairs from the KV store."""
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
        """Prepare the context for JSON serialization."""
        return {
            "store_name": self.store_name,
            "data": await self.get_all(),
        }

    async def to_json(self) -> str:
        """Return the serialized JSON string for the context."""
        serializable_data = await self.to_serializable()
        return json.dumps(serializable_data)
