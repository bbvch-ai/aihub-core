import hashlib
import logging

from redis.asyncio import Redis

from swiss_ai_hub.core.dispatcher.stores.store_base import StoreBase
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent

logger = logging.getLogger(__name__)


class StepStore(StoreBase):
    """
    A execution context-scoped store for tracking step execution data, such as whether the execution has crashed
    and how many times each step has executed.

    ### Why StepStore?
    In complex workflows, steps may have execution limits (e.g., "this step can execution at most 3 times").
    Additionally, if the execution crashes, we need a way to mark that state so other consumers know
    not to proceed with further steps. The StepStore stores this metadata in a JetStream KV
    store, ensuring all instances share a consistent view.

    ### Key Operations
    - **mark_execution_context_as_crashed(execution_context_id)**:
      Marks the execution as crashed, preventing future steps from executing.

    - **is_execution_crashed(execution_context_id)**:
      Checks if a execution is flagged as crashed.

    - **mark_execution_context_as_completed(execution_context_id)**:
      Marks the execution as completed after teardown, so redelivered events are recognised as duplicates.

    - **is_execution_context_completed(execution_context_id)**:
      Checks if an execution has already been torn down.

    - **get_execution_count(execution_context_id, step_name)**:
      Returns how many times a particular step has already been triggered for the execution context.

    - **increment_execution_count(execution_context_id, step_name)**:
      Increments the execution count for a given step, ensuring we never exceed defined limits.

    ### Persistence Details
    - Each execution gets its own KV store
    - Keys include:
      - "crashed": Indicates if the execution is crashed.
      - For execution counts, one key per execution with pattern: step_name.counter.{timestamp}.{random}
    - Default TTL and storage settings inherited from `StoreBase`.

    ### Example
    If a step `my_step` can only execute 2 times, after executing once we call `increment_execution_count`.
    If we try again, we first call `get_execution_count` to ensure we're not over the limit.
    """

    def __init__(self, redis: Redis):
        super().__init__(redis, prefix="steps")

    async def mark_execution_context_as_crashed(self, execution_context_id: str):
        """Flags the execution context as crashed."""
        await self.put_value(execution_context_id, "crashed", b"true")
        logger.debug(f"Marked execution context {execution_context_id} as crashed")

    async def is_execution_context_crashed(self, execution_context_id: str) -> bool:
        """Checks if the execution context has been marked as crashed."""

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        is_crashed = await self.get_value(
            execution_context_id, "crashed", default_value=False, transform_func=transform_to_bool
        )
        if is_crashed:
            logger.debug(f"Execution context {execution_context_id} is crashed")
        return is_crashed

    async def mark_execution_context_as_completed(self, execution_context_id: str) -> None:
        """Flags the execution context as completed, marking that its run has been torn down."""
        await self.put_value(execution_context_id, "completed", b"true")
        logger.debug(f"Marked execution context {execution_context_id} as completed")

    async def is_execution_context_completed(self, execution_context_id: str) -> bool:
        """Checks if the execution context has been marked as completed."""

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        is_completed = await self.get_value(
            execution_context_id, "completed", default_value=False, transform_func=transform_to_bool
        )
        if is_completed:
            logger.debug(f"Execution context {execution_context_id} is completed")
        return is_completed

    async def get_execution_count(self, execution_context_id: str, step_name: str) -> int:
        """Retrieves how many times a given step has executed."""
        counter_key = f"{step_name}.counter"
        count = await self.get_value(
            execution_context_id, counter_key, default_value=0, transform_func=lambda v: int(v) if v is not None else 0
        )
        logger.debug(f"Retrieved execution count {count} for step '{step_name}'")
        return count

    async def increment_execution_count(self, execution_context_id: str, step_name: str):
        """Increments the execution count using a Redis atomic counter."""
        counter_key = f"{step_name}.counter"
        count = await self.increment_counter(execution_context_id, counter_key)
        logger.debug(f"Incremented execution counter to {count} for step '{step_name}'")

    async def was_called_with_events(
        self, execution_context_id: str, step_name: str, events: list[ControlEvent]
    ) -> bool:
        """Checks if a step was called with a specific set of events."""
        key = self._events_to_key(step_name, events)

        def transform_to_bool(value):
            return value is not None and value.decode() == "true"

        return await self.get_value(execution_context_id, key, default_value=False, transform_func=transform_to_bool)

    async def report_execution_context_with_events(
        self, execution_context_id: str, step_name: str, events: list[ControlEvent]
    ):
        """Reports that an execution context was called with a specific set of events."""
        key = self._events_to_key(step_name, events)
        await self.put_value(execution_context_id, key, b"true")
        logger.debug(f"Reported execution context {execution_context_id} with events {key} for step {step_name}")

    def _events_to_key(self, step_name: str, events: list[ControlEvent]) -> str:
        """Builds a unique key for a step and a list of events."""
        sorted_events = sorted(events, key=lambda e: e.event_id)
        events_list = "_".join([event.event_id for event in sorted_events])
        md5_hash = hashlib.md5(events_list.encode()).hexdigest()
        return f"{step_name}.parameters.{md5_hash}"
