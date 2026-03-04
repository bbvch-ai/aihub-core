from pydantic import BaseModel


class BackupContext(BaseModel):
    """Passed from backup_session to per-service backup assets."""

    timestamp: str
    s3_prefix: str
    previously_running: list[str] = []


class RestoreContext(BaseModel):
    """Passed from restore_session to per-service restore assets."""

    timestamp: str
