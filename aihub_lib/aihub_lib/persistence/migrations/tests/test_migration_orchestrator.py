"""
Tests for the migration orchestrator and end-to-end migration workflows.

Tests the complete migration system including orchestration logic,
version detection, and multi-migration scenarios.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from aihub_lib.persistence.base.schema_version import CURRENT_SCHEMA_VERSION
from aihub_lib.persistence.migrations.migrate import MIGRATIONS, MigrationOrchestrator, run_migrations
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

# Migration test fixtures now inline - no external dependencies needed

enable_logging()


async def create_test_docs(db, collection: str, count: int, version: int = 1):
    """Create test documents for migration testing."""
    docs = []
    for i in range(count):
        docs.append({
            "schema_version": version,
            "agent_class": f"TestAgent{i}",
            "agent_id": f"agent_{i}",
            "event_id": f"event_{i}",
            "event_data": {"created_at": 1640995200000000000 + i * 1000000000},
        })
    if docs:
        await db[collection].insert_many(docs)
    return len(docs)


@pytest_asyncio.fixture(scope="function")
async def migration_db():
    """Create test database for migration testing."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings

    mongodb_url = MongoSettings().CONNECTION_STRING.get_secret_value()
    client = AsyncIOMotorClient(mongodb_url)
    db = client["test_migrations"]

    # Clean up any existing test data
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    # Clean up after test
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


class TestMigrationOrchestrator:
    """Test the migration orchestration logic."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database for testing."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        return mock_db

    @pytest.fixture
    def orchestrator(self, mock_db):
        """Create MigrationOrchestrator instance."""
        return MigrationOrchestrator(mock_db)

    @pytest.mark.asyncio
    async def test_get_current_version_with_no_documents(self, orchestrator, mock_db):
        """Test version detection when no documents exist."""
        # Mock empty collection
        mock_db["agent_events"].find_one = AsyncMock(return_value=None)
        mock_db["process_events"].find_one = AsyncMock(return_value=None)

        version = await orchestrator.get_current_version()
        assert version == CURRENT_SCHEMA_VERSION

    @pytest.mark.asyncio
    async def test_get_current_version_with_v1_documents(self, orchestrator, mock_db):
        """Test version detection with v1 documents."""
        # Mock documents at v1
        mock_db["agent_events"].find_one = AsyncMock(return_value={"schema_version": 1})
        mock_db["process_events"].find_one = AsyncMock(return_value={"schema_version": 1})

        version = await orchestrator.get_current_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_get_current_version_with_mixed_versions(self, orchestrator, mock_db):
        """Test version detection with mixed document versions."""
        # Mock mixed versions (should return minimum)
        mock_db["agent_events"].find_one = AsyncMock(return_value={"schema_version": 2})
        mock_db["process_events"].find_one = AsyncMock(return_value={"schema_version": 1})

        version = await orchestrator.get_current_version()
        assert version == 1  # Minimum version

    @pytest.mark.asyncio
    async def test_get_current_version_with_legacy_documents(self, orchestrator, mock_db):
        """Test version detection with documents that have no schema_version field."""
        # Mock legacy documents without schema_version
        mock_db["agent_events"].find_one = AsyncMock(return_value={"event_id": "test"})
        mock_db["process_events"].find_one = AsyncMock(return_value={"event_id": "test"})

        version = await orchestrator.get_current_version()
        assert version == 1  # Assume v1 for legacy documents

    @pytest.mark.asyncio
    async def test_migrate_to_same_version(self, orchestrator, mock_db):
        """Test that migration to same version is a no-op."""
        # Mock current version matches target
        with patch.object(orchestrator, "get_current_version", return_value=2):
            await orchestrator.migrate_to(2)

        # Should not call any migration methods
        assert not any(hasattr(call, "up") for call in mock_db.method_calls)

    @pytest.mark.asyncio
    async def test_migrate_up_single_version(self, orchestrator, mock_db):
        """Test migrating up by one version."""
        # Mock current version is 1, target is 2
        with patch.object(orchestrator, "get_current_version", return_value=1):
            with patch.object(orchestrator, "_migrate_up") as mock_migrate_up:
                await orchestrator.migrate_to(2)
                mock_migrate_up.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_migrate_down_single_version(self, orchestrator, mock_db):
        """Test migrating down by one version."""
        # Mock current version is 2, target is 1
        with patch.object(orchestrator, "get_current_version", return_value=2):
            with patch.object(orchestrator, "_migrate_down") as mock_migrate_down:
                await orchestrator.migrate_to(1)
                mock_migrate_down.assert_called_once_with(2, 1)

    @pytest.mark.asyncio
    async def test_migrate_to_latest(self, orchestrator, mock_db):
        """Test migrating to latest version (None target)."""
        with patch.object(orchestrator, "get_current_version", return_value=1):
            with patch.object(orchestrator, "_migrate_up") as mock_migrate_up:
                await orchestrator.migrate_to(None)  # Should use CURRENT_SCHEMA_VERSION
                mock_migrate_up.assert_called_once_with(1, CURRENT_SCHEMA_VERSION)

    @pytest.mark.asyncio
    async def test_migrate_up_calls_migration_methods(self, orchestrator, mock_db):
        """Test that _migrate_up calls the correct migration methods."""
        # Create a real migration instance to test with
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "validate_prerequisites", return_value=True):
                with patch.object(migration_instance, "up", return_value={"test": "stats"}) as mock_up:
                    await orchestrator._migrate_up(1, 2)

                    mock_up.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_migrate_up_with_failed_prerequisites(self, orchestrator, mock_db):
        """Test that migration fails when prerequisites are not met."""
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "validate_prerequisites", return_value=False):
                with pytest.raises(RuntimeError, match="Prerequisites not met"):
                    await orchestrator._migrate_up(1, 2)

    @pytest.mark.asyncio
    async def test_migrate_down_calls_migration_methods(self, orchestrator, mock_db):
        """Test that _migrate_down calls the correct migration methods."""
        migration_instance = DocumentV2Migrator()

        with patch.object(DocumentV2Migrator, "__new__", return_value=migration_instance):
            with patch.object(migration_instance, "down", return_value={"test": "stats"}) as mock_down:
                await orchestrator._migrate_down(2, 1)

                mock_down.assert_called_once_with(mock_db)


class TestRunMigrations:
    """Test the main run_migrations entry point."""

    @pytest.fixture
    def mock_mongo_client(self):
        """Create mock MongoDB client."""
        mock_client = Mock()
        mock_db = Mock()
        mock_client.__getitem__ = Mock(return_value=mock_db)
        return mock_client

    @pytest.mark.asyncio
    async def test_run_migrations_with_defaults(self, mock_mongo_client):
        """Test run_migrations with default parameters."""
        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_mongo_client):
            with patch.object(MigrationOrchestrator, "migrate_to") as mock_migrate_to:
                await run_migrations("mongodb://test", "test_db")

                mock_migrate_to.assert_called_once_with(None)  # None = latest version

    @pytest.mark.asyncio
    async def test_run_migrations_with_target_version(self, mock_mongo_client):
        """Test run_migrations with specific target version."""
        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_mongo_client):
            with patch.object(MigrationOrchestrator, "migrate_to") as mock_migrate_to:
                await run_migrations("mongodb://test", "test_db", target_version=1)

                mock_migrate_to.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_run_migrations_closes_client(self, mock_mongo_client):
        """Test that MongoDB client is properly closed after migration."""
        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_mongo_client):
            with patch.object(MigrationOrchestrator, "migrate_to"):
                await run_migrations("mongodb://test", "test_db")

                mock_mongo_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_migrations_closes_client_on_exception(self, mock_mongo_client):
        """Test that MongoDB client is closed even when migration fails."""
        with patch("aihub_lib.persistence.migrations.migrate.MongoClient", return_value=mock_mongo_client):
            with patch.object(MigrationOrchestrator, "migrate_to", side_effect=Exception("Migration failed")):
                with pytest.raises(Exception, match="Migration failed"):
                    await run_migrations("mongodb://test", "test_db")

                mock_mongo_client.close.assert_called_once()


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


class TestMigrationOrchestratorIntegration:
    """Integration tests with real MongoDB for migration orchestrator."""

    @pytest.mark.asyncio
    async def test_full_migration_cycle(self, migration_db: AsyncIOMotorDatabase):
        """Test complete migration cycle: setup -> migrate up -> migrate down."""
        # Create test data at v1
        await create_test_docs(migration_db, "agent_events", 10)
        await create_test_docs(migration_db, "process_events", 5)

        orchestrator = MigrationOrchestrator(migration_db)

        # Verify initial state and migrate up
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
        # Create larger test dataset
        await create_test_docs(migration_db, "agent_events", 1000)
        await create_test_docs(migration_db, "process_events", 500)

        orchestrator = MigrationOrchestrator(migration_db)

        # Time the migration
        import time
        start_time = time.time()
        await orchestrator.migrate_to(2)
        duration = time.time() - start_time

        # Should complete within reasonable time
        assert duration < 10.0  # 10 seconds for 1500 documents

        # Verify all documents were migrated
        agent_count = await migration_db["agent_events"].count_documents({"schema_version": 2})
        process_count = await migration_db["process_events"].count_documents({"schema_version": 2})
        assert agent_count == 1000
        assert process_count == 500

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_db: AsyncIOMotorDatabase):
        """Test that running the same migration multiple times is safe."""
        # Create test data
        await create_test_docs(migration_db, "agent_events", 10)

        orchestrator = MigrationOrchestrator(migration_db)

        # Run migration to v2 multiple times
        await orchestrator.migrate_to(2)
        v2_count_1 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        await orchestrator.migrate_to(2)  # Run again
        v2_count_2 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        await orchestrator.migrate_to(2)  # Run third time
        v2_count_3 = await migration_db["agent_events"].count_documents({"schema_version": 2})

        # Stats should be identical after first migration
        assert v2_count_1 == v2_count_2 == v2_count_3 == 10
        v1_count = await migration_db["agent_events"].count_documents({"schema_version": 1})
        assert v1_count == 0  # No v1 documents should remain
