import logging
from typing import Annotated

from nats.js import JetStreamContext

from aihub_agent.dispatchers.stores.StoreBase import StoreBase

logger = logging.getLogger(__name__)


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
        This is a simple put operation that doesn't need concurrency control.
        """
        kv = await self._get_kv_store(run_id)
        await kv.put("crashed", b"true")

    async def is_run_crashed(self, run_id: str) -> bool:
        """Checks if the run has been marked as crashed."""

        # Using the generic get_value method with a transform function
        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        return await self.get_value(run_id, "crashed", default_value=False, transform_func=transform_to_bool)

    async def get_execution_count(self, run_id: str, step_name: str) -> int:
        """Retrieves how many times a given step has executed for the specified run."""
        # Using JSON interface for simplicity, storing as a number
        count = await self.get_json_value(run_id, step_name, default_value=0)
        return count

    async def increment_execution_count(self, run_id: Annotated[str, "Run ID"], step_name: Annotated[str, "Step name"]):
        """
        Increments the execution count for the given step.
        Uses synchronized_update to handle concurrent increments safely.
        """

        # Define update function for synchronized increment
        def increment_count(current_count):
            if current_count is None:
                current_count = 0

            new_count = current_count + 1
            logger.debug(f"Incrementing execution count for step '{step_name}' to {new_count}")
            return new_count

        # Perform synchronized update
        success = await self.synchronized_update(run_id, step_name, increment_count, default_value=0)

        if not success:
            # Emergency fallback
            logger.warning(f"Failed to increment execution count for step '{step_name}'. Using emergency fallback.")
            try:
                current = await self.get_execution_count(run_id, step_name)
                await self.put_json_value(run_id, step_name, current + 1)
            except Exception as e:
                logger.error(f"Emergency fallback for step '{step_name}' also failed: {e}")
                # Last resort - just set to 1
                await self.put_json_value(run_id, step_name, 1)
