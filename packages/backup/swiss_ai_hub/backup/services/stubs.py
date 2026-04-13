from typing import Any, override

from swiss_ai_hub.backup.services.base import BackupHandler


class _StubHandler(BackupHandler):
    """Base for stub handlers that raise NotImplementedError."""

    _name: str = ""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    @property
    @override
    def service_name(self) -> str:
        return self._name

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        raise NotImplementedError(f"{self._name} backup not yet implemented")

    @override
    def restore(self, backup_prefix: str) -> None:
        raise NotImplementedError(f"{self._name} restore not yet implemented")


class MilvusHandler(_StubHandler):
    _name = "Milvus"


class Neo4jHandler(_StubHandler):
    _name = "Neo4j"


class ClickHouseHandler(_StubHandler):
    _name = "ClickHouse"


class NatsHandler(_StubHandler):
    _name = "NATS"
