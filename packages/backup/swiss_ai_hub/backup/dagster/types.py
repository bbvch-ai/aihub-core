from pydantic import BaseModel


class BackupContext(BaseModel):
    """Passed from backup_session to downstream backup assets."""

    timestamp: str
    s3_prefix: str
    previously_running: list[str] = []


class RestoreContext(BaseModel):
    """Passed from restore_session to per-service restore assets."""

    timestamp: str


class MaintenanceContext(BaseModel):
    """Passed from maintenance_session to per-handler maintenance assets.

    Maintenance does NOT stop containers (online-safe by design), so this
    context is much simpler than ``BackupContext`` — just an ID to
    correlate logs across the handlers in one run.
    """

    timestamp: str
    run_id: str
