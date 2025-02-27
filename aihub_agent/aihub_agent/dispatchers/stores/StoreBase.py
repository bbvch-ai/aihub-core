import asyncio
import json
import logging
from datetime import timedelta
from typing import Annotated, Any, Callable, Dict, TypeVar

from nats.js import JetStreamContext
from nats.js.api import KeyValueConfig, StorageType
from nats.js.errors import KeyNotFoundError
from nats.js.kv import KeyValue

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Generic type for value transformation


class StoreBase:
    """
    A base class for run-specific storage in JetStream KV stores with race condition protection.

    ### Why StoreBase?
    In workflows, run-specific data (such as events, step counts, or other metadata) must be preserved
    between steps and even across server restarts. `StoreBase` provides a standardized way to manage
    these per-run key-value stores:
    - Creates a dedicated KV bucket for each run.
    - Ensures data has a reasonable TTL to avoid indefinite growth.
    - Simplifies cleanup at the end of a run.

    ### Key Concepts
    - **Per-Run Stores:** Each run gets its own bucket (e.g., `events_RUNID`, `steps_RUNID`) keyed by `prefix`.
      This isolation prevents conflicts and keeps data organized.
    - **TTL and History:** By default, a TTL ensures stale data is eventually cleaned up, and history=1 keeps only
      the latest value for each key, minimizing storage usage.
    - **On-Demand Creation:** KV stores are created upon first request for a given run, or retrieved if already exists.

    ### Example
    Derived classes like `DistributedEventStore` or `DistributedStepStore` extend `StoreBase` to store run-specific
    events or step execution data. They rely on `_get_kv_store(run_id)` to get the appropriate KV store, then read/write keys.

    ### Lifecycle
    - At run start, when data is first stored for that run, a KV bucket is created if not existing.
    - During the run, data is written to this store.
    - At run end (StopEvent), `delete_run_store` removes the bucket, freeing up space.

    """

    def __init__(
        self,
        js: Annotated[JetStreamContext, "JetStream context for KV store operations."],
        prefix: Annotated[str, "A prefix for bucket naming, ensuring uniqueness."],
    ):
        self.js = js
        self.prefix = prefix
        self._kv_stores: Dict[str, Any] = {}
        self.max_retries = 5
        self.base_backoff = 0.01  # 10ms initial backoff

    async def _get_kv_store(
        self, run_id: Annotated[str, "The run identifier for which we need a KV store."]
    ) -> KeyValue:
        """Retrieves (and if necessary, creates) the KV store for a given run_id."""
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
                # If the bucket already exists, we just retrieve it
                self._kv_stores[run_id] = await self.js.key_value(f"{self.prefix}_{run_id}")
        return self._kv_stores[run_id]

    async def delete_run_store(
        self,
        run_id: Annotated[str, "The run identifier whose store should be deleted."],
    ):
        """
        Deletes the KV store for a specific run, removing all associated data.
        Also clears any cached references in _kv_stores.

        Use this at run completion to reclaim resources and maintain a clean state.
        """
        if run_id in self._kv_stores:
            await self.js.delete_key_value(f"{self.prefix}_{run_id}")
            del self._kv_stores[run_id]

    async def get_value(
        self, run_id: str, key: str, default_value: T = None, transform_func: Callable[[bytes], T] = None
    ) -> T:
        """Retrieves a value from the store, optionally transforming it with a provided function."""
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get(key)
            if transform_func:
                return transform_func(entry.value)
            return entry.value  # type: ignore
        except KeyNotFoundError:
            return default_value
        except Exception as e:
            logger.error(f"Error retrieving key '{key}': {e}")
            return default_value

    async def put_json_value(self, run_id: str, key: str, value: Any) -> bool:
        """Stores a JSON-serializable value in the KV store."""
        kv = await self._get_kv_store(run_id)
        try:
            serialized = json.dumps(value).encode()
            await kv.put(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error storing JSON value for key '{key}': {e}")
            return False

    async def get_json_value(self, run_id: str, key: str, default_value: Any = None) -> Any:
        """Retrieves and deserializes a JSON value from the KV store."""

        def json_transform(value_bytes):
            return json.loads(value_bytes.decode())

        return await self.get_value(run_id, key, default_value, json_transform)

    async def atomic_operation(
        self,
        run_id: str,
        operation_func: Callable[[], Any],
        max_attempts: int = None,
    ) -> Any:
        """
        Executes an operation with retry logic for handling transient errors.

        This is useful for operations that might have temporary failures in a distributed
        environment but don't have built-in optimistic concurrency control.
        """
        attempts = 0
        max_attempts = max_attempts or self.max_retries

        while attempts < max_attempts:
            try:
                result = await operation_func()
                return result
            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    logger.error(f"Operation failed after {attempts} attempts: {e}")
                    return None

                backoff = self.base_backoff * (2**attempts)
                logger.debug(f"Operation failed, retrying ({attempts}/{max_attempts}) after {backoff:.4f}s: {e}")
                await asyncio.sleep(backoff)

        return None

    async def synchronized_update(
        self, run_id: str, key: str, update_func: Callable[[Any], Any], default_value: Any = None
    ) -> bool:
        """
        Performs a synchronized update on a JSON value using a mutex pattern.

        Since the NATS JetStream KeyValue API doesn't appear to support native optimistic
        concurrency control, we create a mutex key specifically for this operation.
        """
        # Create a mutex key to synchronize access
        mutex_key = f"mutex_{key}"
        kv = await self._get_kv_store(run_id)

        # Try to acquire the mutex
        max_attempts = 10
        attempts = 0
        mutex_acquired = False

        while attempts < max_attempts and not mutex_acquired:
            try:
                # Try to create the mutex
                try:
                    await kv.create(mutex_key, b"locked")
                    mutex_acquired = True
                except Exception:
                    # Mutex already exists, wait and retry
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.warning(f"Failed to acquire mutex for key '{key}' after {attempts} attempts")
                        return False

                    backoff = self.base_backoff * (2**attempts)
                    logger.debug(f"Waiting for mutex ({attempts}/{max_attempts}): {key}")
                    await asyncio.sleep(backoff)
            except Exception as e:
                logger.error(f"Error acquiring mutex for key '{key}': {e}")
                return False

        if not mutex_acquired:
            return False

        try:
            # Read current value
            current_value = await self.get_json_value(run_id, key, default_value)

            # Apply update function
            new_value = update_func(current_value)

            # Store updated value
            success = await self.put_json_value(run_id, key, new_value)
            return success

        finally:
            # Always release the mutex, even if the update fails
            try:
                await kv.delete(mutex_key)
            except Exception as e:
                logger.error(f"Error releasing mutex for key '{key}': {e}")
