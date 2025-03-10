import hashlib
import logging
from typing import List

from aihub_lib.nats.events import ControlEvent
from redis.asyncio import Redis

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

    def __init__(self, redis: Redis):
        super().__init__(redis, prefix="steps")

    async def mark_run_as_crashed(self, run_id: str):
        """Flags the run as crashed."""
        await self.put_value(run_id, "crashed", b"true")
        logger.debug(f"Marked run {run_id} as crashed")

    async def is_run_crashed(self, run_id: str) -> bool:
        """Checks if the run has been marked as crashed."""

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        return await self.get_value(run_id, "crashed", default_value=False, transform_func=transform_to_bool)

    async def get_execution_count(self, run_id: str, step_name: str) -> int:
        """Retrieves how many times a given step has executed."""
        counter_key = f"{step_name}.counter"
        count = await self.get_value(
            run_id, counter_key, default_value=0, transform_func=lambda v: int(v) if v is not None else 0
        )
        logger.debug(f"Retrieved execution count {count} for step '{step_name}'")
        return count

    async def increment_execution_count(self, run_id: str, step_name: str):
        """Increments the execution count using a Redis atomic counter."""
        counter_key = f"{step_name}.counter"
        count = await self.increment_counter(run_id, counter_key)
        logger.debug(f"Incremented execution counter to {count} for step '{step_name}'")

    async def was_called_with_events(self, run_id: str, step_name: str, events: List[ControlEvent]) -> bool:
        """Checks if a step was called with a specific set of events."""
        key = self._events_to_key(step_name, events)

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        return await self.get_value(run_id, key, default_value=False, transform_func=transform_to_bool)

    async def report_run_with_events(self, run_id: str, step_name: str, events: List[ControlEvent]):
        """Reports that a run was called with a specific set of events."""
        key = self._events_to_key(step_name, events)
        await self.put_value(run_id, key, b"true")
        logger.debug(f"Reported run {run_id} with events {key} for step {step_name}")

    def _events_to_key(self, step_name: str, events: List[ControlEvent]) -> str:
        """Builds a unique key for a step and a list of events."""
        sorted_events = sorted(events, key=lambda e: e.event_id)
        events_list = "_".join([event.event_id for event in sorted_events])
        md5_hash = hashlib.md5(events_list.encode()).hexdigest()
        return f"{step_name}.parameters.{md5_hash}"
