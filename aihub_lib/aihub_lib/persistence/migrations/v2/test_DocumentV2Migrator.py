"""Tests for DocumentV2Migrator - consolidated and simplified."""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


@pytest_asyncio.fixture
async def migration_db():
    """Create test database for DocumentV2Migrator testing."""
    client = AsyncIOMotorClient(MongoSettings().CONNECTION_STRING.get_secret_value())
    db = client["test_v2_migration"]

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


class TestDocumentV2Migrator:
    """Comprehensive tests for DocumentV2Migrator."""

    def test_migration_properties(self):
        """Test that migration has correct properties."""
        migration = DocumentV2Migrator()
        assert migration.version == 2
        assert "created_at" in migration.description
        assert "V2" in migration.__class__.__name__
        assert len(migration.description) > 50
        assert migration.__class__.__doc__ is not None
        assert len(migration.__class__.__doc__.strip()) > 100

        collections = migration.get_affected_collections()
        assert "agent_events" in collections
        assert "process_events" in collections

    @pytest.mark.asyncio
    async def test_up_migration_mock(self):
        """Test the up migration with mocked database."""
        migration = DocumentV2Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_result = Mock()
        mock_result.modified_count = 100
        mock_result.matched_count = 100
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.create_index = AsyncMock()

        result = await migration.up(mock_db)
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result

    @pytest.mark.asyncio
    async def test_down_migration_mock(self):
        """Test the down migration with mocked database."""
        migration = DocumentV2Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_result = Mock()
        mock_result.modified_count = 75
        mock_result.matched_count = 75
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.drop_index = AsyncMock()

        result = await migration.down(mock_db)
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result

    @pytest.mark.asyncio
    async def test_validate_prerequisites(self):
        """Test prerequisite validation."""
        migration = DocumentV2Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.count_documents = AsyncMock(return_value=0)
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events"])
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        result = await migration.validate_prerequisites(mock_db)
        assert result is True

    @pytest.mark.asyncio
    async def test_migration_with_realistic_data(self, migration_db):
        """Test migration with realistic data."""
        v1_docs = [
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "agent_001",
                "event_id": "event_001",
                "event_data": {"created_at": 1640995200000000000, "content": "Test content"},
            },
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "agent_002",
                "event_id": "event_002",
                "event_data": {"created_at": 1640995260000000000, "content": "Another test"},
            },
        ]

        await migration_db["agent_events"].insert_many(v1_docs)
        migration = DocumentV2Migrator()
        result = await migration.up(migration_db)

        assert result["agent_events"]["modified"] == 2
        assert result["agent_events"]["matched"] == 2

        # Verify data transformation
        docs = await migration_db["agent_events"].find({}).to_list(length=None)
        for doc in docs:
            assert doc["schema_version"] == 2
            assert "created_at" in doc
            assert doc["created_at"] == doc["event_data"]["created_at"]

    @pytest.mark.asyncio
    async def test_migration_rollback_integrity(self, migration_db):
        """Test that rollback properly restores original state."""
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "rollback_test",
            "event_id": "rollback_event",
            "event_data": {"created_at": 1640995200000000000, "content": "Rollback test"},
        }

        await migration_db["agent_events"].insert_one(test_doc)
        migration = DocumentV2Migrator()

        # Migrate up and verify
        await migration.up(migration_db)
        migrated_doc = await migration_db["agent_events"].find_one({"event_id": "rollback_event"})
        assert migrated_doc["schema_version"] == 2
        assert "created_at" in migrated_doc

        # Rollback and verify
        await migration.down(migration_db)
        rolled_back_doc = await migration_db["agent_events"].find_one({"event_id": "rollback_event"})
        assert rolled_back_doc["schema_version"] == 1
        assert "created_at" not in rolled_back_doc or rolled_back_doc.get("created_at") is None
        assert rolled_back_doc["event_data"]["created_at"] == 1640995200000000000

    @pytest.mark.asyncio
    async def test_migration_handles_missing_created_at(self, migration_db):
        """Test migration behavior with documents missing created_at."""
        problematic_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "problematic_agent",
            "event_id": "problematic_event",
            "event_data": {"content": "Document without created_at"},
        }

        await migration_db["agent_events"].insert_one(problematic_doc)
        migration = DocumentV2Migrator()
        await migration.up(migration_db)

        doc = await migration_db["agent_events"].find_one({"event_id": "problematic_event"})

        if doc["schema_version"] == 2:
            # If migrated, created_at should be null when source was missing
            if "created_at" in doc:
                assert doc["created_at"] is None or doc["created_at"] == ""
        else:
            # If skipped, should remain at v1
            assert doc["schema_version"] == 1

    @pytest.mark.asyncio
    async def test_migration_performance(self, migration_db):
        """Test migration performance with medium dataset."""
        docs = [
            {
                "schema_version": 1,
                "agent_class": f"TestAgent{i % 10}",
                "agent_id": f"agent_{i:03d}",
                "event_id": f"event_{i:03d}",
                "event_data": {"created_at": 1640995200000000000 + (i * 1000000000), "content": f"Test {i}"},
            }
            for i in range(100)
        ]

        await migration_db["agent_events"].insert_many(docs)

        import time

        migration = DocumentV2Migrator()

        start_time = time.time()
        result = await migration.up(migration_db)
        duration = time.time() - start_time

        assert duration < 5.0  # 5 seconds for 100 documents
        assert result["agent_events"]["modified"] == 100
        assert result["agent_events"]["matched"] == 100

        # Verify all documents migrated correctly
        migrated_count = await migration_db["agent_events"].count_documents({"schema_version": 2})
        assert migrated_count == 100

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_db):
        """Test that running the same migration multiple times is safe."""
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "idempotent_test",
            "event_id": "idempotent_event",
            "event_data": {"created_at": 1640995200000000000, "content": "Idempotent test"},
        }

        await migration_db["agent_events"].insert_one(test_doc)
        migration = DocumentV2Migrator()

        # Run migration multiple times
        result1 = await migration.up(migration_db)
        result2 = await migration.up(migration_db)
        result3 = await migration.up(migration_db)

        # First run should modify the document
        assert result1["agent_events"]["modified"] == 1

        # Subsequent runs should not modify already migrated documents
        assert result2["agent_events"]["modified"] == 0
        assert result3["agent_events"]["modified"] == 0

        # Verify document is correctly migrated
        final_doc = await migration_db["agent_events"].find_one({"event_id": "idempotent_event"})
        assert final_doc["schema_version"] == 2
        assert final_doc["created_at"] == 1640995200000000000
        assert final_doc["event_data"]["created_at"] == 1640995200000000000

    @pytest.mark.asyncio
    async def test_migration_validates_input_parameters(self):
        """Test that migration validates input parameters properly."""
        migration = DocumentV2Migrator()

        # Should handle None database gracefully
        with pytest.raises((TypeError, AttributeError)):
            await migration.up(None)

        with pytest.raises((TypeError, AttributeError)):
            await migration.down(None)
