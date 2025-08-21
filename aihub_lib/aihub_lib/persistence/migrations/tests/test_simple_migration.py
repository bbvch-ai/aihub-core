"""Simple migration tests without complex patterns."""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.migrations.migrate import MIGRATIONS, MigrationOrchestrator
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


@pytest_asyncio.fixture
async def migration_db():
    """Create test database for migration testing."""
    client = AsyncIOMotorClient(MongoSettings().CONNECTION_STRING.get_secret_value())
    db = client["test_migrations_simple"]

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


class TestMigrationBasics:
    """Basic migration tests using mocks and real database."""

    def test_migration_class_properties(self):
        """Test that migration has required properties."""
        migration = DocumentV2Migrator()
        assert migration.version == 2
        assert "created_at" in migration.description
        assert "agent_events" in migration.get_affected_collections()
        assert "process_events" in migration.get_affected_collections()

    @pytest.mark.asyncio
    async def test_migration_up_with_mock_db(self):
        """Test migration up with mocked database operations."""
        migration = DocumentV2Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events"])

        mock_result = Mock()
        mock_result.modified_count = 5
        mock_result.matched_count = 5
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.create_index = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=5)

        stats = await migration.up(mock_db)
        assert isinstance(stats, dict)
        assert "agent_events" in stats
        assert "process_events" in stats
        assert mock_collection.update_many.call_count >= 2
        assert mock_collection.create_index.call_count >= 8

    @pytest.mark.asyncio
    async def test_migration_down_with_mock_db(self):
        """Test migration down with mocked database operations."""
        migration = DocumentV2Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events"])

        mock_result = Mock()
        mock_result.modified_count = 3
        mock_result.matched_count = 3
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.drop_index = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=3)

        stats = await migration.down(mock_db)
        assert isinstance(stats, dict)
        assert "agent_events" in stats
        assert "process_events" in stats
        assert mock_collection.update_many.call_count >= 2
        assert mock_collection.drop_index.call_count >= 6

    def test_migration_is_registered(self):
        """Test that DocumentV2Migrator is properly registered."""
        assert DocumentV2Migrator in MIGRATIONS
        versions = [migration.version for migration in MIGRATIONS]
        assert len(versions) == len(set(versions)), "Migration versions should be unique"

        versions = sorted(versions)
        for i in range(1, len(versions)):
            assert versions[i] == versions[i - 1] + 1, f"Versions should be sequential: {versions}"

    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """Test that orchestrator can be created with mock database."""
        mock_db = Mock()
        orchestrator = MigrationOrchestrator(mock_db)
        assert orchestrator.db == mock_db
        assert len(orchestrator.migrations) >= 1

    @pytest.mark.asyncio
    async def test_get_current_version_with_mocked_collections(self):
        """Test version detection with mocked collections."""
        mock_db = Mock()
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events"])
        
        mock_collection = Mock()
        mock_collection.find_one = AsyncMock(return_value={"schema_version": 1})
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        orchestrator = MigrationOrchestrator(mock_db)
        version = await orchestrator.get_current_version()
        assert version == 1

    @pytest.mark.asyncio
    async def test_migration_with_real_data(self, migration_db):
        """Test migration with real MongoDB and realistic data."""
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "test_agent_1",
            "event_id": "test_event_1",
            "event_data": {"created_at": 1640995200000000000, "content": "Test content"},
        }

        await migration_db["agent_events"].insert_one(test_doc)

        migration = DocumentV2Migrator()
        stats = await migration.up(migration_db)
        assert stats["agent_events"]["modified"] == 1

        # Check that document was properly migrated
        doc = await migration_db["agent_events"].find_one({"event_id": "test_event_1"})
        assert doc["schema_version"] == 2
        assert doc["created_at"] == 1640995200000000000
        assert doc["event_data"]["created_at"] == 1640995200000000000

    @pytest.mark.asyncio
    async def test_migration_rollback(self, migration_db):
        """Test that migration can be properly rolled back."""
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "test_agent_rollback",
            "event_id": "test_event_rollback",
            "event_data": {"created_at": 1640995200000000000, "content": "Test rollback content"},
        }

        await migration_db["agent_events"].insert_one(test_doc)
        migration = DocumentV2Migrator()

        # Migrate up and verify
        await migration.up(migration_db)
        doc = await migration_db["agent_events"].find_one({"event_id": "test_event_rollback"})
        assert doc["schema_version"] == 2
        assert "created_at" in doc

        # Rollback and verify
        await migration.down(migration_db)
        doc = await migration_db["agent_events"].find_one({"event_id": "test_event_rollback"})
        assert doc["schema_version"] == 1
        assert "created_at" not in doc or doc.get("created_at") is None
        assert doc["event_data"]["created_at"] == 1640995200000000000
