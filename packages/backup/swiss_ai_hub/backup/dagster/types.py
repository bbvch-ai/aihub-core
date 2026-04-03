from pydantic import BaseModel


class BackupContext(BaseModel):
    """Passed from backup_session to downstream backup assets."""

    timestamp: str
    s3_prefix: str
    previously_running: list[str] = []
