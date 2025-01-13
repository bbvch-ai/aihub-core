from datetime import timedelta
from typing import Annotated, Any, Dict

from nats.js import JetStreamContext
from nats.js.api import KeyValueConfig, StorageType


class StoreBase:
    """
    A base class for run-specific storage in JetStream KV stores.

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

    async def _get_kv_store(
        self, run_id: Annotated[str, "The run identifier for which we need a KV store."]
    ) -> Any:
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
                self._kv_stores[run_id] = await self.js.key_value(
                    f"{self.prefix}_{run_id}"
                )
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
