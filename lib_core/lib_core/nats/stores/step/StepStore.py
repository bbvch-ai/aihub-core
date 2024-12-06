from nats.js import JetStreamContext

from lib_core.nats.stores.StoreBase import StoreBase


class DistributedStepStore(StoreBase):
    def __init__(self, js: JetStreamContext):
        super().__init__(js, prefix="steps")

    async def mark_run_as_crashed(self, run_id: str):
        kv = await self._get_kv_store(run_id)
        await kv.put("crashed", b"true")

    async def is_run_crashed(self, run_id: str) -> bool:
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get("crashed")
            return entry is not None
        except Exception:
            return False

    async def get_execution_count(self, run_id: str, step_name: str) -> int:
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get(step_name)
            count = int(entry.value.decode())
            return count
        except Exception:
            return 0  # If not found, return 0

    async def increment_execution_count(self, run_id: str, step_name: str):
        kv = await self._get_kv_store(run_id)
        count = await self.get_execution_count(run_id, step_name)
        count += 1
        await kv.put(step_name, str(count).encode())
