"""
Simple migration tests that demonstrate the testing approach without complex inheritance.

These tests show how to validate migration functionality using mocks and
real MongoDB when available.
"""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from aihub_lib.persistence.migrations.migrate import MIGRATIONS, MigrationOrchestrator
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

# Migration test fixtures now inline - no external dependencies needed

enable_logging()


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


class TestMigrationBasics:
    """Basic migration tests using mocks - fast and reliable."""

    def test_migration_class_properties(self):
        """Test that migration has required properties."""
        migration = DocumentV2Migrator()

        assert migration.version == 2
        assert migration.description == "Add root-level created_at field for query optimization"
        assert isinstance(migration.get_affected_collections(), list)
        assert "agent_events" in migration.get_affected_collections()
        assert "process_events" in migration.get_affected_collections()

    @pytest.mark.asyncio
    async def test_migration_up_with_mock_db(self):
        """Test migration up with mocked database operations."""
        migration = DocumentV2Migrator()

        # Create mock database and collection
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        # Mock update results
        mock_result = Mock()
        mock_result.modified_count = 5
        mock_result.matched_count = 5
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.create_index = AsyncMock()

        # Execute migration
        stats = await migration.up(mock_db)

        # Validate results
        assert isinstance(stats, dict)
        assert "agent_events" in stats
        assert "process_events" in stats

        # Verify database calls were made
        assert mock_collection.update_many.call_count >= 2  # Once per collection
        assert mock_collection.create_index.call_count >= 8  # Multiple indices per collection

    @pytest.mark.asyncio
    async def test_migration_down_with_mock_db(self):
        """Test migration down with mocked database operations."""
        migration = DocumentV2Migrator()

        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_result = Mock()
        mock_result.modified_count = 3
        mock_result.matched_count = 3
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.drop_index = AsyncMock()

        # Execute rollback
        stats = await migration.down(mock_db)

        # Validate results
        assert isinstance(stats, dict)
        assert "agent_events" in stats
        assert "process_events" in stats

        # Verify rollback calls were made
        assert mock_collection.update_many.call_count >= 2
        assert mock_collection.drop_index.call_count >= 6  # Multiple indices dropped


class TestMigrationRegistration:
    """Test migration registration and orchestration."""

    def test_migration_is_registered(self):
        """Test that DocumentV2Migrator is properly registered."""
        assert DocumentV2Migrator in MIGRATIONS
        assert len(MIGRATIONS) >= 1

    def test_migration_versions_are_unique(self):
        """Test that all migrations have unique version numbers."""
        versions = [migration.version for migration in MIGRATIONS]
        assert len(versions) == len(set(versions)), "Migration versions should be unique"

    def test_migration_versions_are_sequential(self):
        """Test that migration versions form a sequential sequence."""
        versions = sorted([migration.version for migration in MIGRATIONS])
        for i in range(1, len(versions)):
            assert versions[i] == versions[i - 1] + 1, f"Versions should be sequential: {versions}"


class TestMigrationOrchestratorMock:
    """Test migration orchestrator with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """Test that orchestrator can be created with mock database."""
        mock_db = Mock()
        orchestrator = MigrationOrchestrator(mock_db)

        assert orchestrator.db == mock_db
        assert len(orchestrator.migrations) >= 1
        assert orchestrator.migrations[0].version <= orchestrator.migrations[-1].version

    @pytest.mark.asyncio
    async def test_get_current_version_with_mocked_collections(self):
        """Test version detection with mocked collections."""
        mock_db = Mock()

        # Mock collection that returns v1 document
        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value={"schema_version": 1})
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()

        assert version == 1


@pytest.mark.mongodb
class TestMigrationWithRealMongoDB:
    """
    Integration tests that require real MongoDB.

    Run with: pytest tests/persistence/migrations/ --mongodb
    """

    @pytest.mark.asyncio
    async def test_migration_with_real_data(self, migration_test_database):
        """Test migration with real MongoDB and realistic data."""
        # Create test data representing v1 schema
        test_docs = [
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "test_agent_1",
                "thread_id": "test_thread_1",
                "display_id": "test_display_1",
                "run_id": "test_run_1",
                "event_id": "test_event_1",
                "event_type": "display",
                "event_name": "TestEvent",
                "event_data": {
                    "created_at": 1640995200000000000,  # 2022-01-01 00:00:00 in nanoseconds
                    "content": "Test content",
                },
                "event_parents": ["BaseEvent", "DisplayEvent"],
            }
        ]

        # Insert test data
        await migration_test_database["agent_events"].insert_many(test_docs)

        # Run migration
        migration = DocumentV2Migrator()
        stats = await migration.up(migration_test_database)

        # Validate migration results
        assert stats["agent_events"]["modified"] == 1

        # Check that document was properly migrated
        doc = await migration_test_database["agent_events"].find_one({"event_id": "test_event_1"})
        assert doc["schema_version"] == 2
        assert doc["created_at"] == 1640995200000000000  # Root-level created_at matches
        assert doc["event_data"]["created_at"] == 1640995200000000000  # Original preserved

    @pytest.mark.asyncio
    async def test_migration_rollback(self, migration_test_database):
        """Test that migration can be properly rolled back."""
        # Create and migrate test data
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "test_agent_rollback",
            "thread_id": "test_thread_rollback",
            "display_id": "test_display_rollback",
            "run_id": "test_run_rollback",
            "event_id": "test_event_rollback",
            "event_type": "control",
            "event_name": "TestEvent",
            "event_data": {"created_at": 1640995200000000000, "content": "Test rollback content"},
            "event_parents": ["BaseEvent", "ControlEvent"],
        }

        await migration_test_database["agent_events"].insert_one(test_doc)

        migration = DocumentV2Migrator()

        # Migrate up
        await migration.up(migration_test_database)

        # Verify migration
        doc = await migration_test_database["agent_events"].find_one({"event_id": "test_event_rollback"})
        assert doc["schema_version"] == 2
        assert "created_at" in doc  # Root-level field added

        # Rollback
        await migration.down(migration_test_database)

        # Verify rollback
        doc = await migration_test_database["agent_events"].find_one({"event_id": "test_event_rollback"})
        assert doc["schema_version"] == 1
        assert "created_at" not in doc or doc.get("created_at") is None  # Root-level field removed
        assert doc["event_data"]["created_at"] == 1640995200000000000  # Nested field preserved
