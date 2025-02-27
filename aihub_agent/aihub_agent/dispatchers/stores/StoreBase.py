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
        self._kv_stores: Dict[str, KeyValue] = {}
        self.max_retries = 10  # Up to 1 second backoff
        self.base_backoff = 0.001  # 1ms initial backoff

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
                logger.debug(f"Created new KV store '{self.prefix}_{run_id}'")
            except Exception as e:
                if "already in use" in str(e).lower():
                    # If the bucket already exists, we just retrieve it
                    self._kv_stores[run_id] = await self.js.key_value(f"{self.prefix}_{run_id}")
                    logger.debug(f"Using existing KV store '{self.prefix}_{run_id}'")
                else:
                    logger.error(f"Error creating KV store '{self.prefix}_{run_id}': {e}")
                    raise

        return self._kv_stores[run_id]

    async def delete_run_store(
        self,
        run_id: Annotated[str, "The run identifier whose store should be deleted."],
    ):
        """
        Deletes the KV store for a specific run, removing all associated data.
        Also clears any cached references in _kv_stores.
        """
        if run_id in self._kv_stores:
            try:
                await self.js.delete_key_value(f"{self.prefix}_{run_id}")
                del self._kv_stores[run_id]
                logger.debug(f"Deleted KV store '{self.prefix}_{run_id}'")
            except Exception as e:
                logger.error(f"Error deleting KV store '{self.prefix}_{run_id}': {e}")

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

    async def put_value(self, run_id: str, key: str, value: bytes) -> bool:
        """Stores a raw byte value in the KV store."""
        kv = await self._get_kv_store(run_id)
        try:
            await kv.put(key, value)
            return True
        except Exception as e:
            logger.error(f"Error storing value for key '{key}': {e}")
            return False

    async def put_json_value(self, run_id: str, key: str, value: Any) -> bool:
        """Stores a JSON-serializable value in the KV store."""
        try:
            serialized = json.dumps(value).encode()
            return await self.put_value(run_id, key, serialized)
        except Exception as e:
            logger.error(f"Error serializing JSON value for key '{key}': {e}")
            return False

    async def get_json_value(self, run_id: str, key: str, default_value: Any = None) -> Any:
        """Retrieves and deserializes a JSON value from the KV store."""

        def json_transform(value_bytes):
            return json.loads(value_bytes.decode())

        return await self.get_value(run_id, key, default_value, json_transform)

    async def retry_operation(
        self,
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
