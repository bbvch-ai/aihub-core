from abc import ABC, abstractmethod


class BackupHandler(ABC):
    """Synchronous I/O intentionally: Dagster ops execute in a synchronous context,
    and all I/O here is process-local (Docker SDK, subprocess, boto3) where async
    would add complexity without benefit.
    """

    @property
    @abstractmethod
    def service_name(self) -> str: ...

    @abstractmethod
    def backup(self, backup_id: str, s3_prefix: str) -> None: ...

    @abstractmethod
    def restore(self, backup_prefix: str) -> None:
        """``backup_prefix`` is the S3 timestamp prefix, e.g. ``2026-01-15_10-30-00``."""
        ...
