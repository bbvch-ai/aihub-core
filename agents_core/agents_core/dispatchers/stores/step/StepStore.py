from nats.js import JetStreamContext

from agents_core.dispatchers.stores.StoreBase import StoreBase


class DistributedStepStore(StoreBase):
    """
    A run-scoped store for tracking step execution data, such as whether the run has crashed
    and how many times each step has executed.

    ### Why DistributedStepStore?
    In complex workflows, steps may have execution limits (e.g., "this step can run at most 3 times").
    Additionally, if the run crashes, we need a way to mark that state so other consumers know
    not to proceed with further steps. The DistributedStepStore stores this metadata in a JetStream KV
    store, ensuring all instances share a consistent view.

    ### Key Operations
    - **mark_run_as_crashed(run_id)**:
      Marks the run as crashed, preventing future steps from executing.

    - **is_run_crashed(run_id)**:
      Checks if a run is flagged as crashed.

    - **get_execution_count(run_id, step_name)**:
      Returns how many times a particular step has already executed for the run.

    - **increment_execution_count(run_id, step_name)**:
      Increments the execution count for a given step, ensuring we never exceed defined limits.

    ### Persistence Details
    - Each run gets its own KV store (e.g. "steps_RUNID").
    - Keys include:
      - "crashed": Indicates if the run is crashed.
      - A step's name as key, with an integer representing execution count.
    - Default TTL and storage settings inherited from `StoreBase`.

    ### Example
    If a step `my_step` can only run 2 times, after executing once we call `increment_execution_count`.
    If we try again, we first `get_execution_count` to ensure we're not over the limit.

    """

    def __init__(self, js: JetStreamContext):
        super().__init__(js, prefix="steps")

    async def mark_run_as_crashed(self, run_id: str):
        """
        Flags the run as crashed by setting a 'crashed' key.
        Once crashed, steps won't be executed further.
        """
        kv = await self._get_kv_store(run_id)
        await kv.put("crashed", b"true")

    async def is_run_crashed(self, run_id: str) -> bool:
        """
        Checks if the run has been marked as crashed.
        Returns True if so, False otherwise.
        """
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get("crashed")
            return entry is not None
        except Exception:
            return False

    async def get_execution_count(self, run_id: str, step_name: str) -> int:
        """
        Retrieves how many times a given step has executed for the specified run.
        If no count is found, returns 0.
        """
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get(step_name)
            count = int(entry.value.decode())
            return count
        except Exception:
            return 0

    async def increment_execution_count(self, run_id: str, step_name: str):
        """
        Increments the execution count for the given step in the run's store.
        This is used to track how many times a step has been executed, aiding in enforcing limits.
        """
        kv = await self._get_kv_store(run_id)
        count = await self.get_execution_count(run_id, step_name)
        count += 1
        await kv.put(step_name, str(count).encode())
