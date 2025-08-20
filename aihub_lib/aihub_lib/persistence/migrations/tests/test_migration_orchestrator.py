"""Tests for the migration orchestrator and end-to-end migration workflows."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.base.schema_version import CURRENT_SCHEMA_VERSION
from aihub_lib.persistence.migrations.migrate import MIGRATIONS, MigrationOrchestrator, run_migrations
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


@pytest_asyncio.fixture
async def migration_db():
    """Create test database for migration testing."""
    client = AsyncIOMotorClient(MongoSettings().CONNECTION_STRING.get_secret_value())
    db = client["test_migrations"]

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


async def create_test_docs(db, collection: str, count: int, version: int = 1):
    """Create test documents for migration testing."""
    docs = [
        {
            "schema_version": version,
            "agent_class": f"TestAgent{i}",
            "agent_id": f"agent_{i}",
            "event_id": f"event_{i}",
            "event_data": {"created_at": 1640995200000000000 + i * 1000000000},
        }
        for i in range(count)
    ]

    if docs:
        await db[collection].insert_many(docs)
    return len(docs)


class TestMigrationOrchestrator:
    """Test the migration orchestration logic."""

    @pytest.mark.asyncio
    async def test_get_current_version_with_no_documents(self):
        """Test version detection when no documents exist."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()
        assert version == CURRENT_SCHEMA_VERSION

    @pytest.mark.asyncio
    async def test_get_current_version_with_v1_documents(self):
        """Test version detection with v1 documents."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value={"schema_version": 1})
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_get_current_version_with_mixed_versions(self):
        """Test version detection with mixed document versions."""
        mock_db = Mock()
        mock_agent_collection = Mock()
        mock_process_collection = Mock()
        mock_agent_collection.find_one = AsyncMock(return_value={"schema_version": 2})
        mock_process_collection.find_one = AsyncMock(return_value={"schema_version": 1})

        def get_collection(name):
            if name == "agent_events":
                return mock_agent_collection
            elif name == "process_events":
                return mock_process_collection
            return Mock()

        mock_db.__getitem__ = Mock(side_effect=get_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_get_current_version_with_legacy_documents(self):
        """Test version detection with documents that have no schema_version field."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value={"event_id": "test"})
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_migrate_to_same_version(self):
        """Test that migration to same version is a no-op."""
        mock_db = Mock()
        orchestrator = MigrationOrchestrator(mock_db)

        with patch.object(orchestrator, "get_current_version", return_value=2):
            await orchestrator.migrate_to(2)

        assert not any(hasattr(call, "up") for call in mock_db.method_calls)

    @pytest.mark.asyncio
    async def test_migrate_up_single_version(self):
        """Test migrating up by one version."""
        orchestrator = MigrationOrchestrator(Mock())

        with patch.object(orchestrator, "get_current_version", return_value=1):
            with patch.object(orchestrator, "_migrate_up") as mock_migrate_up:
                await orchestrator.migrate_to(2)
                mock_migrate_up.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_migrate_down_single_version(self):
        """Test migrating down by one version."""
        orchestrator = MigrationOrchestrator(Mock())

        with patch.object(orchestrator, "get_current_version", return_value=2):
            with patch.object(orchestrator, "_migrate_down") as mock_migrate_down:
                await orchestrator.migrate_to(1)
                mock_migrate_down.assert_called_once_with(2, 1)

    @pytest.mark.asyncio
    async def test_migrate_to_latest(self):
        """Test migrating to latest version (None target)."""
        orchestrator = MigrationOrchestrator(Mock())

        with patch.object(orchestrator, "get_current_version", return_value=1):
            with patch.object(orchestrator, "_migrate_up") as mock_migrate_up:
                await orchestrator.migrate_to(None)
                mock_migrate_up.assert_called_once_with(1, CURRENT_SCHEMA_VERSION)

    @pytest.mark.asyncio
    async def test_migrate_up_calls_migration_methods(self):
        """Test that _migrate_up calls the correct migration methods."""
        mock_db = Mock()
        orchestrator = MigrationOrchestrator(mock_db)
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "validate_prerequisites", return_value=True):
                with patch.object(migration_instance, "up", return_value={"test": "stats"}) as mock_up:
                    await orchestrator._migrate_up(1, 2)
                    mock_up.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_migrate_up_with_failed_prerequisites(self):
        """Test that migration fails when prerequisites are not met."""
        orchestrator = MigrationOrchestrator(Mock())
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "validate_prerequisites", return_value=False):
                with pytest.raises(RuntimeError, match="Prerequisites not met"):
                    await orchestrator._migrate_up(1, 2)

    @pytest.mark.asyncio
    async def test_migrate_down_calls_migration_methods(self):
        """Test that _migrate_down calls the correct migration methods."""
        mock_db = Mock()
        orchestrator = MigrationOrchestrator(mock_db)
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "down", return_value={"test": "stats"}) as mock_down:
                await orchestrator._migrate_down(2, 1)
                mock_down.assert_called_once_with(mock_db)


class TestRunMigrations:
    """Test the main run_migrations entry point."""

    @pytest.mark.asyncio
    async def test_run_migrations_with_defaults(self):
        """Test run_migrations with default parameters."""
        mock_client = Mock()
        mock_client.__getitem__ = Mock(return_value=Mock())

        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_client):
            with patch.object(MigrationOrchestrator, "migrate_to") as mock_migrate_to:
                await run_migrations("mongodb://test", "test_db")
                mock_migrate_to.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_run_migrations_with_target_version(self):
        """Test run_migrations with specific target version."""
        mock_client = Mock()
        mock_client.__getitem__ = Mock(return_value=Mock())

        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_client):
            with patch.object(MigrationOrchestrator, "migrate_to") as mock_migrate_to:
                await run_migrations("mongodb://test", "test_db", target_version=1)
                mock_migrate_to.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_run_migrations_closes_client(self):
        """Test that MongoDB client is properly closed after migration."""
        mock_client = Mock()
        mock_client.__getitem__ = Mock(return_value=Mock())

        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_client):
            with patch.object(MigrationOrchestrator, "migrate_to"):
                await run_migrations("mongodb://test", "test_db")
                mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_migrations_closes_client_on_exception(self):
        """Test that MongoDB client is closed even when migration fails."""
        mock_client = Mock()
        mock_client.__getitem__ = Mock(return_value=Mock())

        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_client):
            with patch.object(MigrationOrchestrator, "migrate_to", side_effect=Exception("Migration failed")):
                with pytest.raises(Exception, match="Migration failed"):
                    await run_migrations("mongodb://test", "test_db")
                mock_client.close.assert_called_once()


class TestMigrationRegistration:
    """Test migration registration and discovery."""

    def test_migrations_list_contains_expected_migrations(self):
        """Test that MIGRATIONS list contains expected migration classes."""
        assert len(MIGRATIONS) >= 1
        assert DocumentV2Migrator in MIGRATIONS

    def test_migrations_are_sorted_by_version(self):
        """Test that migrations are properly sorted by version number."""
        versions = [migration.version for migration in MIGRATIONS]
        assert versions == sorted(versions), "Migrations should be sorted by version number"

    def test_no_duplicate_migration_versions(self):
        """Test that no two migrations have the same version."""
        versions = [migration.version for migration in MIGRATIONS]
        assert len(versions) == len(set(versions)), "Migration versions should be unique"

    def test_migration_versions_are_sequential(self):
        """Test that migration versions form a sequential sequence."""
        versions = [migration.version for migration in MIGRATIONS]
        if len(versions) > 1:
            for i in range(1, len(versions)):
                assert versions[i] == versions[i - 1] + 1, f"Migration versions should be sequential: {versions}"


class TestMigrationIntegration:
    """Integration tests with real MongoDB for migration orchestrator."""

    @pytest.mark.asyncio
    async def test_full_migration_cycle(self, migration_db: AsyncIOMotorDatabase):
        """Test complete migration cycle: setup -> migrate up -> migrate down."""
        await create_test_docs(migration_db, "agent_events", 10)
        await create_test_docs(migration_db, "process_events", 5)
        orchestrator = MigrationOrchestrator(migration_db)

        # Migrate up
        assert await orchestrator.get_current_version() == 1
        await orchestrator.migrate_to(2)
        assert await orchestrator.get_current_version() == 2

        # Verify migration worked
        agent_doc = await migration_db["agent_events"].find_one({})
        assert agent_doc["schema_version"] == 2
        assert "created_at" in agent_doc

        # Migrate down and verify rollback
        await orchestrator.migrate_to(1)
        assert await orchestrator.get_current_version() == 1
        agent_doc = await migration_db["agent_events"].find_one({})
        assert agent_doc["schema_version"] == 1
        assert "created_at" not in agent_doc

    @pytest.mark.asyncio
    async def test_migration_with_large_dataset(self, migration_db: AsyncIOMotorDatabase):
        """Test migration performance with larger dataset."""
        await create_test_docs(migration_db, "agent_events", 1000)
        await create_test_docs(migration_db, "process_events", 500)
        orchestrator = MigrationOrchestrator(migration_db)

        import time

        start_time = time.time()
        await orchestrator.migrate_to(2)
        duration = time.time() - start_time

        assert duration < 10.0  # 10 seconds for 1500 documents

        agent_count = await migration_db["agent_events"].count_documents({"schema_version": 2})
        process_count = await migration_db["process_events"].count_documents({"schema_version": 2})
        assert agent_count == 1000
        assert process_count == 500

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_db: AsyncIOMotorDatabase):
        """Test that running the same migration multiple times is safe."""
        await create_test_docs(migration_db, "agent_events", 10)
        orchestrator = MigrationOrchestrator(migration_db)

        # Run migration multiple times
        await orchestrator.migrate_to(2)
        v2_count_1 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        await orchestrator.migrate_to(2)
        v2_count_2 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        await orchestrator.migrate_to(2)
        v2_count_3 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        assert v2_count_1 == v2_count_2 == v2_count_3 == 10
        v1_count = await migration_db["agent_events"].count_documents({"schema_version": 1})
        assert v1_count == 0
