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


class MigrationTestHelper:
    """Inline migration test helper."""

    async def create_bulk_test_data(self, db, collection_name: str, count: int, schema_version: int = 1):
        """Create bulk test data for migration testing."""
        docs = []
        for i in range(count):
            doc = {
                "schema_version": schema_version,
                "agent_class": f"TestAgent{i}",
                "agent_id": f"test_agent_{i}",
                "thread_id": f"test_thread_{i}",
                "display_id": f"test_display_{i}",
                "run_id": f"test_run_{i}",
                "event_id": f"test_event_{i}",
                "event_type": "display",
                "event_name": f"TestEvent{i}",
                "event_data": {
                    "created_at": 1640995200000000000 + i * 1000000000,
                    "content": f"Test content {i}",
                },
                "event_parents": ["BaseEvent", "DisplayEvent"],
            }
            docs.append(doc)

        if docs:
            await db[collection_name].insert_many(docs)

    async def verify_collection_schema_version(self, db, collection_name: str, expected_version: int) -> bool:
        """Verify all documents in collection have expected schema version."""
        doc = await db[collection_name].find_one({"schema_version": {"$ne": expected_version}})
        return doc is None

    async def get_collection_stats(self, db, collection_name: str) -> dict:
        """Get collection statistics including version counts."""
        pipeline = [{"$group": {"_id": "$schema_version", "count": {"$sum": 1}}}]
        cursor = db[collection_name].aggregate(pipeline)
        results = await cursor.to_list(length=None)

        version_counts = {}
        for result in results:
            version_counts[result["_id"]] = result["count"]

        return {"version_counts": version_counts, "total_docs": sum(version_counts.values())}


@pytest_asyncio.fixture(scope="function")
async def migration_test_database():
    """Create test database for migration testing."""
    from motor.motor_asyncio import AsyncIOMotorClient

    from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings

    mongodb_url = MongoSettings().CONNECTION_STRING.get_secret_value()
    client = AsyncIOMotorClient(mongodb_url)
    db_name = "test_migrations"
    db = client[db_name]

    # Clean up any existing test data
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    # Clean up after test
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


@pytest.fixture
def migration_test_helper():
    """Provide migration test helper instance."""
    return MigrationTestHelper()


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


@pytest.mark.mongodb
class TestMigrationOrchestratorIntegration:
    """Integration tests with real MongoDB for migration orchestrator."""

    @pytest.mark.asyncio
    async def test_full_migration_cycle(self, migration_test_database: AsyncIOMotorDatabase):
        """Test complete migration cycle: setup -> migrate up -> migrate down."""
        # Create test data at v1
        helper = MigrationTestHelper()
        await helper.create_bulk_test_data(migration_test_database, "agent_events", 10, schema_version=1)
        await helper.create_bulk_test_data(migration_test_database, "process_events", 5, schema_version=1)

        orchestrator = MigrationOrchestrator(migration_test_database)

        # Verify initial state
        initial_version = await orchestrator.get_current_version()
        assert initial_version == 1

        # Migrate up to v2
        await orchestrator.migrate_to(2)

        # Verify migration to v2
        current_version = await orchestrator.get_current_version()
        assert current_version == 2

        # Verify data integrity after migration up
        assert await helper.verify_collection_schema_version(migration_test_database, "agent_events", 2)
        assert await helper.verify_collection_schema_version(migration_test_database, "process_events", 2)

        # Verify created_at field was added
        agent_doc = await migration_test_database["agent_events"].find_one({})
        assert "created_at" in agent_doc
        assert agent_doc["created_at"] == agent_doc["event_data"]["created_at"]

        # Migrate down to v1
        await orchestrator.migrate_to(1)

        # Verify rollback to v1
        rollback_version = await orchestrator.get_current_version()
        assert rollback_version == 1

        # Verify data integrity after rollback
        assert await helper.verify_collection_schema_version(migration_test_database, "agent_events", 1)
        assert await helper.verify_collection_schema_version(migration_test_database, "process_events", 1)

        # Verify created_at field was removed
        agent_doc = await migration_test_database["agent_events"].find_one({})
        assert "created_at" not in agent_doc
        assert "created_at" in agent_doc["event_data"]  # Still in event_data

    @pytest.mark.asyncio
    async def test_migration_with_large_dataset(self, migration_test_database: AsyncIOMotorDatabase):
        """Test migration performance with larger dataset."""
        # Create larger test dataset
        helper = MigrationTestHelper()
        await helper.create_bulk_test_data(migration_test_database, "agent_events", 1000, schema_version=1)
        await helper.create_bulk_test_data(migration_test_database, "process_events", 500, schema_version=1)

        orchestrator = MigrationOrchestrator(migration_test_database)

        # Time the migration
        import time

        start_time = time.time()
        await orchestrator.migrate_to(2)
        duration = time.time() - start_time

        # Should complete within reasonable time
        assert duration < 10.0  # 10 seconds for 1500 documents

        # Verify all documents were migrated
        helper = MigrationTestHelper()
        stats = await helper.get_collection_stats(migration_test_database, "agent_events")
        assert stats["version_counts"][2] == 1000

        stats = await helper.get_collection_stats(migration_test_database, "process_events")
        assert stats["version_counts"][2] == 500

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_test_database: AsyncIOMotorDatabase):
        """Test that running the same migration multiple times is safe."""
        # Create test data
        helper = MigrationTestHelper()
        await helper.create_bulk_test_data(migration_test_database, "agent_events", 10, schema_version=1)

        orchestrator = MigrationOrchestrator(migration_test_database)

        # Run migration to v2 multiple times
        await orchestrator.migrate_to(2)
        stats1 = await helper.get_collection_stats(migration_test_database, "agent_events")

        await orchestrator.migrate_to(2)  # Run again
        stats2 = await helper.get_collection_stats(migration_test_database, "agent_events")

        await orchestrator.migrate_to(2)  # Run third time
        stats3 = await helper.get_collection_stats(migration_test_database, "agent_events")

        # Stats should be identical after first migration
        assert stats1 == stats2 == stats3
        assert stats1["version_counts"][2] == 10
        assert 1 not in stats1["version_counts"]  # No v1 documents should remain
