import logging
import random
import time
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
      - For execution counts, one key per execution with pattern: step_name.counter.{timestamp}.{random}
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
        await self.put_value(run_id, "crashed", b"true")
        logger.debug(f"Marked run {run_id} as crashed")

    async def is_run_crashed(self, run_id: str) -> bool:
        """
        Checks if the run has been marked as crashed.
        Returns True if so, False otherwise.
        """

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        return await self.get_value(run_id, "crashed", default_value=False, transform_func=transform_to_bool)

    async def get_execution_count(self, run_id: str, step_name: str) -> int:
        """
        Retrieves how many times a given step has executed for the specified run
        by counting individual counter keys.

        This method is always accurate because it directly counts the keys rather than
        relying on a cached value.
        """
        kv = await self._get_kv_store(run_id)

        try:
            # Get all keys
            all_keys = await kv.keys()

            # Filter keys for this step's counters
            counter_prefix = f"{step_name}.counter."
            counter_keys = [key for key in all_keys if key.startswith(counter_prefix)]
            count = len(counter_keys)

            logger.debug(f"Counted {count} executions for step '{step_name}'")
            return count

        except Exception as e:
            logger.error(f"Error counting executions for step '{step_name}': {e}")
            return 0

    async def increment_execution_count(self, run_id: Annotated[str, "Run ID"], step_name: Annotated[str, "Step name"]):
        """
        Increments the execution count by creating a unique counter key for this execution.
        This approach completely avoids race conditions as each execution creates its own key.
        """
        # Create a unique counter key for this execution with timestamp and random component
        unique_id = f"{int(time.time() * 1000)}.{random.randint(1000, 9999)}"
        counter_key = f"{step_name}.counter.{unique_id}"

        # Store the counter (value doesn't matter, just the existence of the key)
        success = await self.put_value(run_id, counter_key, b"1")

        if success:
            logger.debug(f"Created execution counter {counter_key} for step '{step_name}'")
        else:
            logger.error(f"Failed to create execution counter for step '{step_name}'")
