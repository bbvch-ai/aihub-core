from datetime import timedelta
from typing import Dict, Any
from nats.js import JetStreamContext
from nats.js.api import KeyValueConfig, StorageType


class StoreBase:
    def __init__(self, js: JetStreamContext, prefix: str):
        self.js = js
        self.prefix = prefix
        self._kv_stores: Dict[str, Any] = {}

    async def _get_kv_store(self, run_id: str):
        if run_id not in self._kv_stores:
            try:
                self._kv_stores[run_id] = await self.js.create_key_value(
                    KeyValueConfig(
                        bucket=f"{self.prefix}_{run_id}",
                        history=1,
                        ttl=timedelta(hours=1).seconds,
                        storage=StorageType.FILE,
                    )
                )
            except Exception:
                self._kv_stores[run_id] = await self.js.key_value(f"{self.prefix}_{run_id}")
        return self._kv_stores[run_id]

    async def delete_run_store(self, run_id: str):
        if run_id in self._kv_stores:
            await self.js.delete_key_value(f"{self.prefix}_{run_id}")
            del self._kv_stores[run_id]
