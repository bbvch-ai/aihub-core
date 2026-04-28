from abc import ABC, abstractmethod

from pydantic import BaseModel


class MaintenanceResult(BaseModel):
    """Outcome of a single maintenance handler run.

    Mirrors ``ServiceResult`` but carries handler-specific metadata
    (rows affected, sizes before/after) so the Dagster UI surfaces what
    each pass did. ``rows_affected`` is None for handlers that don't
    delete rows (index migrations, autovacuum tuning).
    """

    name: str
    succeeded: bool
    duration_seconds: float = 0.0
    rows_affected: int | None = None
    error: str | None = None
    metadata: dict[str, str | int | float] = {}


class MaintenanceHandler(ABC):
    """Synchronous I/O — same rationale as BackupHandler.

    Each handler performs one maintenance task (a delete query, an index
    migration, a repack) against the platform Postgres. Handlers must be
    idempotent: the schedule re-runs them weekly/monthly forever.
    """

    @property
    @abstractmethod
    def service_name(self) -> str: ...

    @abstractmethod
    def run(self) -> MaintenanceResult: ...
