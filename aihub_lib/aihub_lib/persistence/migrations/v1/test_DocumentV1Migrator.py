"""Tests for DocumentV1Migrator - consolidated and simplified."""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.migrations.v1.DocumentV1Migrator import DocumentV1Migrator
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


@pytest_asyncio.fixture
async def migration_db():
    """Create test database for DocumentV1Migrator testing."""
    client = AsyncIOMotorClient(MongoSettings().CONNECTION_STRING.get_secret_value())
    db = client["test_v1_migration"]

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


class TestDocumentV1Migrator:
    """Comprehensive tests for DocumentV1Migrator."""

    def test_migration_properties(self):
        """Test that migration has correct properties."""
        migration = DocumentV1Migrator()
        assert migration.version == 1
        assert "schema_version" in migration.description
        assert "V1" in migration.__class__.__name__
        assert len(migration.description) > 20
        assert migration.__class__.__doc__ is not None
        assert len(migration.__class__.__doc__.strip()) > 50

        # V1 migration affects ALL collections, so get_affected_collections() returns []
        collections = migration.get_affected_collections()
        assert collections == []

    @pytest.mark.asyncio
    async def test_up_migration_mock(self):
        """Test the up migration with mocked database."""
        migration = DocumentV1Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events", "user_profiles"])

        mock_result = Mock()
        mock_result.modified_count = 50
        mock_result.matched_count = 50
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.create_index = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=50)

        result = await migration.up(mock_db)
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result
        assert "user_profiles" in result  # All collections should be processed

    @pytest.mark.asyncio
    async def test_down_migration_mock(self):
        """Test the down migration with mocked database."""
        migration = DocumentV1Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events", "user_profiles"])

        mock_result = Mock()
        mock_result.modified_count = 25
        mock_result.matched_count = 25
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        mock_collection.drop_index = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=25)

        result = await migration.down(mock_db)
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result
        assert "user_profiles" in result  # All collections should be processed

    @pytest.mark.asyncio
    async def test_validate_prerequisites(self):
        """Test prerequisite validation."""
        migration = DocumentV1Migrator()
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.count_documents = AsyncMock(return_value=0)
        mock_db.list_collection_names = AsyncMock(return_value=[])  # Empty collections list should still validate
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        result = await migration.validate_prerequisites(mock_db)
        assert result is True

    @pytest.mark.asyncio
    async def test_migration_with_realistic_data(self, migration_db):
        """Test migration with realistic data."""
        v0_docs = [
            {
                "agent_class": "TestAgent",
                "agent_id": "agent_001",
                "event_id": "event_001",
                "event_data": {"created_at": 1640995200000000000, "content": "Test content"},
            },
            {
                "agent_class": "TestAgent",
                "agent_id": "agent_002",
                "event_id": "event_002",
                "event_data": {"created_at": 1640995260000000000, "content": "Another test"},
            },
        ]

        await migration_db["agent_events"].insert_many(v0_docs)
        migration = DocumentV1Migrator()
        result = await migration.up(migration_db)

        assert result["agent_events"]["modified"] == 2
        assert result["agent_events"]["matched"] == 2

        # Verify data transformation
        docs = await migration_db["agent_events"].find({}).to_list(length=None)
        for doc in docs:
            assert doc["schema_version"] == 1

    @pytest.mark.asyncio
    async def test_migration_rollback_integrity(self, migration_db):
        """Test that rollback properly restores original state."""
        test_doc = {
            "agent_class": "TestAgent",
            "agent_id": "rollback_test",
            "event_id": "rollback_event",
            "event_data": {"created_at": 1640995200000000000, "content": "Rollback test"},
        }

        await migration_db["agent_events"].insert_one(test_doc)
        migration = DocumentV1Migrator()

        # Migrate up and verify
        await migration.up(migration_db)
        migrated_doc = await migration_db["agent_events"].find_one({"event_id": "rollback_event"})
        assert migrated_doc["schema_version"] == 1

        # Rollback and verify
        await migration.down(migration_db)
        rolled_back_doc = await migration_db["agent_events"].find_one({"event_id": "rollback_event"})
        assert "schema_version" not in rolled_back_doc

    @pytest.mark.asyncio
    async def test_migration_performance(self, migration_db):
        """Test migration performance with medium dataset."""
        docs = [
            {
                "agent_class": f"TestAgent{i % 10}",
                "agent_id": f"agent_{i:03d}",
                "event_id": f"event_{i:03d}",
                "event_data": {"created_at": 1640995200000000000 + (i * 1000000000), "content": f"Test {i}"},
            }
            for i in range(100)
        ]

        await migration_db["agent_events"].insert_many(docs)

        import time

        migration = DocumentV1Migrator()

        start_time = time.time()
        result = await migration.up(migration_db)
        duration = time.time() - start_time

        assert duration < 5.0  # 5 seconds for 100 documents
        assert result["agent_events"]["modified"] == 100
        assert result["agent_events"]["matched"] == 100

        # Verify all documents migrated correctly
        migrated_count = await migration_db["agent_events"].count_documents({"schema_version": 1})
        assert migrated_count == 100

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_db):
        """Test that running the same migration multiple times is safe."""
        test_doc = {
            "agent_class": "TestAgent",
            "agent_id": "idempotent_test",
            "event_id": "idempotent_event",
            "event_data": {"created_at": 1640995200000000000, "content": "Idempotent test"},
        }

        await migration_db["agent_events"].insert_one(test_doc)
        migration = DocumentV1Migrator()

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
        assert final_doc["schema_version"] == 1

    @pytest.mark.asyncio
    async def test_migration_validates_input_parameters(self):
        """Test that migration validates input parameters properly."""
        migration = DocumentV1Migrator()

        # Should handle None database gracefully
        with pytest.raises((TypeError, AttributeError)):
            await migration.up(None)

        with pytest.raises((TypeError, AttributeError)):
            await migration.down(None)

    @pytest.mark.asyncio
    async def test_migration_skips_documents_with_schema_version(self, migration_db):
        """Test that migration skips documents that already have schema_version."""
        docs_with_schema = [
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "agent_with_schema",
                "event_id": "event_with_schema",
                "event_data": {"created_at": 1640995200000000000, "content": "Already has schema"},
            },
            {
                "schema_version": 2,
                "agent_class": "TestAgent", 
                "agent_id": "agent_v2",
                "event_id": "event_v2",
                "event_data": {"created_at": 1640995260000000000, "content": "V2 document"},
            },
        ]

        docs_without_schema = [
            {
                "agent_class": "TestAgent",
                "agent_id": "agent_without_schema", 
                "event_id": "event_without_schema",
                "event_data": {"created_at": 1640995320000000000, "content": "No schema version"},
            }
        ]

        all_docs = docs_with_schema + docs_without_schema
        await migration_db["agent_events"].insert_many(all_docs)
        
        migration = DocumentV1Migrator()
        result = await migration.up(migration_db)

        # Should only modify the one document without schema_version
        assert result["agent_events"]["modified"] == 1
        assert result["agent_events"]["matched"] == 1

        # Verify the document without schema_version now has it
        doc_without_schema = await migration_db["agent_events"].find_one({"event_id": "event_without_schema"})
        assert doc_without_schema["schema_version"] == 1

        # Verify documents with schema_version are unchanged
        doc_with_schema = await migration_db["agent_events"].find_one({"event_id": "event_with_schema"})
        assert doc_with_schema["schema_version"] == 1  # unchanged

        doc_v2 = await migration_db["agent_events"].find_one({"event_id": "event_v2"})
        assert doc_v2["schema_version"] == 2  # unchanged

    @pytest.mark.asyncio
    async def test_migration_processes_all_collections(self, migration_db):
        """Test that migration processes ALL collections in the database."""
        # Create documents in multiple collections
        await migration_db["agent_events"].insert_one({
            "agent_class": "TestAgent",
            "event_data": {"created_at": 1640995200000000000}
        })
        
        await migration_db["process_events"].insert_one({
            "process_id": "test_process",
            "data": {"value": "test"}
        })
        
        await migration_db["user_profiles"].insert_one({
            "user_id": "test_user",
            "name": "Test User"
        })
        
        migration = DocumentV1Migrator()
        result = await migration.up(migration_db)
        
        # All collections should be in the result
        assert "agent_events" in result
        assert "process_events" in result  
        assert "user_profiles" in result
        
        # Verify all documents got schema_version
        agent_doc = await migration_db["agent_events"].find_one({})
        assert agent_doc["schema_version"] == 1
        
        process_doc = await migration_db["process_events"].find_one({})
        assert process_doc["schema_version"] == 1
        
        user_doc = await migration_db["user_profiles"].find_one({})
        assert user_doc["schema_version"] == 1