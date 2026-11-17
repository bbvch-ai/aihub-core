from pydantic import BaseModel


class OpenWebuiModWorkerState(BaseModel):
    pid: int
    version: int
    error: str | None
    ready: bool
    updated_at: float
