import pytest

from swiss_ai_hub.backup.dagster.assets.handler_factory import HANDLER_FACTORIES, create_handler
from swiss_ai_hub.backup.models import BACKUP_SERVICES
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.services.clickhouse import ClickHouseHandler
from swiss_ai_hub.backup.services.milvus import MilvusHandler
from swiss_ai_hub.backup.services.nats import NatsHandler
from swiss_ai_hub.backup.services.neo4j import Neo4jHandler
from swiss_ai_hub.backup.services.postgres import PostgresHandler
from swiss_ai_hub.backup.services.valkey import ValkeyHandler


def test_handler_factories_covers_all_services() -> None:
    assert set(HANDLER_FACTORIES.keys()) == set(BACKUP_SERVICES)


@pytest.mark.parametrize(
    ("service_name", "expected_type"),
    [
        ("PostgreSQL", PostgresHandler),
        ("Milvus", MilvusHandler),
        ("Neo4j", Neo4jHandler),
        ("ClickHouse", ClickHouseHandler),
        ("Valkey", ValkeyHandler),
        ("NATS", NatsHandler),
    ],
)
def test_create_handler_returns_correct_type(service_name: str, expected_type: type[BackupHandler]) -> None:
    handler = create_handler(service_name, None, None, None)  # type: ignore[arg-type]
    assert isinstance(handler, expected_type)
    assert handler.service_name == service_name


def test_create_handler_raises_for_unknown_service() -> None:
    with pytest.raises(KeyError):
        create_handler("UnknownService", None, None, None)  # type: ignore[arg-type]
