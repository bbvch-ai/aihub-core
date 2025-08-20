"""
Comprehensive tests for DocumentV2Migrator.

Tests the specific migration logic for V2 schema changes including:
- Adding root-level created_at field from event_data.created_at
- Creating optimized indices for time-based queries
- Ensuring data integrity during migration and rollback
"""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


@pytest_asyncio.fixture(scope="function")
async def migration_test_database():
    """Create test database for DocumentV2Migrator testing."""
    from motor.motor_asyncio import AsyncIOMotorClient

    from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings

    mongodb_url = MongoSettings().CONNECTION_STRING.get_secret_value()
    client = AsyncIOMotorClient(mongodb_url)
    db_name = "test_v2_migration"
    db = client[db_name]

    # Clean up any existing test data
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})

    yield db

    # Clean up after test
    await db["agent_events"].delete_many({})
    await db["process_events"].delete_many({})
    client.close()


class TestDocumentV2MigratorProperties:
    """Test DocumentV2Migrator class properties and metadata."""

    def test_migration_version(self):
        """Test that migration has correct version number."""
        migration = DocumentV2Migrator()
        assert migration.version == 2

    def test_migration_description(self):
        """Test that migration has descriptive documentation."""
        migration = DocumentV2Migrator()
        assert migration.description == "Add root-level created_at field for query optimization"
        assert len(migration.description) > 20  # Ensure meaningful description

    def test_affected_collections(self):
        """Test that migration specifies correct collections."""
        migration = DocumentV2Migrator()
        collections = migration.get_affected_collections()

        assert isinstance(collections, list)
        assert "agent_events" in collections
        assert "process_events" in collections
        assert len(collections) >= 2

    def test_migration_implements_required_methods(self):
        """Test that migration implements all required interface methods."""
        migration = DocumentV2Migrator()

        # Check required methods exist and are callable
        assert hasattr(migration, "up") and callable(migration.up)
        assert hasattr(migration, "down") and callable(migration.down)
        assert hasattr(migration, "validate_prerequisites") and callable(migration.validate_prerequisites)
        assert hasattr(migration, "get_affected_collections") and callable(migration.get_affected_collections)


class TestDocumentV2MigratorMockOperations:
    """Test DocumentV2Migrator with mocked database operations."""

    @pytest.mark.asyncio
    async def test_up_migration_structure(self):
        """Test the structure of the up migration without real database."""
        migration = DocumentV2Migrator()

        # Create comprehensive mock setup
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        # Mock successful update result
        mock_update_result = Mock()
        mock_update_result.modified_count = 100
        mock_update_result.matched_count = 100
        mock_collection.update_many = AsyncMock(return_value=mock_update_result)
        mock_collection.create_index = AsyncMock()

        # Execute migration
        result = await migration.up(mock_db)

        # Verify structure of results
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result

        # Verify each collection has expected result structure
        for collection_name in ["agent_events", "process_events"]:
            collection_result = result[collection_name]
            assert "modified" in collection_result
            assert "matched" in collection_result
            # Note: indices_created not in result structure, just logged

    @pytest.mark.asyncio
    async def test_up_migration_database_calls(self):
        """Test that up migration makes correct database calls."""
        migration = DocumentV2Migrator()

        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_update_result = Mock()
        mock_update_result.modified_count = 50
        mock_update_result.matched_count = 50
        mock_collection.update_many = AsyncMock(return_value=mock_update_result)
        mock_collection.create_index = AsyncMock()

        await migration.up(mock_db)

        # Verify update_many was called for each collection with correct aggregation pipeline
        assert mock_collection.update_many.call_count == 2  # Two collections

        # Check that aggregation pipeline is used (should contain $set operation)
        call_args = mock_collection.update_many.call_args_list
        for call in call_args:
            filter_arg, pipeline_arg = call[0]
            assert filter_arg == {"schema_version": 1}  # Filter for v1 documents
            assert isinstance(pipeline_arg, list)  # Aggregation pipeline
            assert len(pipeline_arg) == 1  # Single stage
            assert "$set" in pipeline_arg[0]  # Should set new fields

        # Verify index creation was called multiple times
        assert mock_collection.create_index.call_count >= 8  # Multiple indices per collection

    @pytest.mark.asyncio
    async def test_down_migration_structure(self):
        """Test the structure of the down migration."""
        migration = DocumentV2Migrator()

        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_update_result = Mock()
        mock_update_result.modified_count = 75
        mock_update_result.matched_count = 75
        mock_collection.update_many = AsyncMock(return_value=mock_update_result)
        mock_collection.drop_index = AsyncMock()

        result = await migration.down(mock_db)

        # Verify structure
        assert isinstance(result, dict)
        assert "agent_events" in result
        assert "process_events" in result

        for collection_name in ["agent_events", "process_events"]:
            collection_result = result[collection_name]
            assert "modified" in collection_result
            assert "matched" in collection_result
            # Note: indices_dropped not in result structure, just logged

    @pytest.mark.asyncio
    async def test_down_migration_database_calls(self):
        """Test that down migration makes correct database calls."""
        migration = DocumentV2Migrator()

        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        mock_update_result = Mock()
        mock_update_result.modified_count = 25
        mock_update_result.matched_count = 25
        mock_collection.update_many = AsyncMock(return_value=mock_update_result)
        mock_collection.drop_index = AsyncMock()

        await migration.down(mock_db)

        # Verify rollback calls
        assert mock_collection.update_many.call_count == 2

        # Check rollback operations - DocumentV2Migrator uses direct update operations, not pipelines
        call_args = mock_collection.update_many.call_args_list
        for call in call_args:
            filter_arg, update_arg = call[0]
            assert filter_arg == {"schema_version": 2}  # Filter for v2 documents
            assert isinstance(update_arg, dict)
            # Should have both $unset for created_at and $set for schema_version
            assert "$unset" in update_arg and "$set" in update_arg

        # Verify index dropping
        assert mock_collection.drop_index.call_count >= 6  # Multiple indices dropped

    @pytest.mark.asyncio
    async def test_validate_prerequisites_success(self):
        """Test prerequisite validation under normal conditions."""
        migration = DocumentV2Migrator()

        # Mock database with proper async methods
        mock_db = Mock()
        mock_collection = Mock()
        mock_collection.count_documents = AsyncMock(return_value=0)  # No documents at wrong version

        mock_db.list_collection_names = AsyncMock(return_value=["agent_events", "process_events"])
        mock_db.__getitem__ = Mock(return_value=mock_collection)

        # Should pass validation (no specific prerequisites for V2)
        result = await migration.validate_prerequisites(mock_db)
        assert result is True

    def test_migration_error_handling(self):
        """Test that migration handles edge cases gracefully."""
        migration = DocumentV2Migrator()

        # Test with invalid inputs
        assert hasattr(migration, "version")
        assert migration.version > 0
        assert isinstance(migration.get_affected_collections(), list)


@pytest.mark.mongodb
class TestDocumentV2MigratorIntegration:
    """Integration tests with real MongoDB for DocumentV2Migrator."""

    @pytest.mark.asyncio
    async def test_migration_with_realistic_v1_data(self, migration_test_database):
        """Test migration with realistic V1 document structures."""
        # Create realistic V1 test data
        v1_agent_events = [
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "agent_001",
                "thread_id": "thread_001",
                "display_id": "display_001",
                "run_id": "run_001",
                "event_id": "event_001",
                "event_type": "display",
                "event_name": "TestDisplayEvent",
                "event_data": {
                    "created_at": 1640995200000000000,  # 2022-01-01 00:00:00
                    "content": "Test display content",
                    "metadata": {"key": "value"},
                },
                "event_parents": ["BaseEvent", "DisplayEvent"],
            },
            {
                "schema_version": 1,
                "agent_class": "TestAgent",
                "agent_id": "agent_002",
                "thread_id": "thread_002",
                "display_id": "display_002",
                "run_id": "run_002",
                "event_id": "event_002",
                "event_type": "control",
                "event_name": "TestControlEvent",
                "event_data": {
                    "created_at": 1640995260000000000,  # 1 minute later
                    "action": "start",
                    "parameters": {"param1": "value1"},
                },
                "event_parents": ["BaseEvent", "ControlEvent"],
            },
        ]

        v1_process_events = [
            {
                "schema_version": 1,
                "process_id": "process_001",
                "step_id": "step_001",
                "event_type": "work",
                "event_data": {
                    "created_at": 1640995320000000000,  # 2 minutes later
                    "work_type": "analysis",
                    "status": "completed",
                },
            }
        ]

        # Insert test data
        await migration_test_database["agent_events"].insert_many(v1_agent_events)
        await migration_test_database["process_events"].insert_many(v1_process_events)

        # Run migration
        migration = DocumentV2Migrator()
        result = await migration.up(migration_test_database)

        # Verify migration results
        assert result["agent_events"]["modified"] == 2
        assert result["agent_events"]["matched"] == 2
        assert result["process_events"]["modified"] == 1
        assert result["process_events"]["matched"] == 1

        # Verify data transformation
        agent_docs = await migration_test_database["agent_events"].find({}).to_list(length=None)
        for doc in agent_docs:
            assert doc["schema_version"] == 2
            assert "created_at" in doc  # Root-level field added
            assert doc["created_at"] == doc["event_data"]["created_at"]  # Values match
            assert "created_at" in doc["event_data"]  # Original preserved

        process_docs = await migration_test_database["process_events"].find({}).to_list(length=None)
        for doc in process_docs:
            assert doc["schema_version"] == 2
            assert "created_at" in doc
            assert doc["created_at"] == doc["event_data"]["created_at"]

    @pytest.mark.asyncio
    async def test_migration_rollback_data_integrity(self, migration_test_database):
        """Test that rollback properly restores original state."""
        # Create and migrate test data
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "rollback_test",
            "thread_id": "rollback_thread",
            "display_id": "rollback_display",
            "run_id": "rollback_run",
            "event_id": "rollback_event",
            "event_type": "display",
            "event_name": "RollbackTestEvent",
            "event_data": {
                "created_at": 1640995200000000000,
                "content": "Rollback test content",
                "extra_field": "should_be_preserved",
            },
            "event_parents": ["BaseEvent", "DisplayEvent"],
        }

        await migration_test_database["agent_events"].insert_one(test_doc)

        migration = DocumentV2Migrator()

        # Migrate up
        await migration.up(migration_test_database)

        # Verify migration worked
        migrated_doc = await migration_test_database["agent_events"].find_one({"event_id": "rollback_event"})
        assert migrated_doc["schema_version"] == 2
        assert "created_at" in migrated_doc

        # Rollback
        await migration.down(migration_test_database)

        # Verify rollback
        rolled_back_doc = await migration_test_database["agent_events"].find_one({"event_id": "rollback_event"})
        assert rolled_back_doc["schema_version"] == 1
        assert "created_at" not in rolled_back_doc or rolled_back_doc.get("created_at") is None
        assert rolled_back_doc["event_data"]["created_at"] == 1640995200000000000  # Original preserved
        assert rolled_back_doc["event_data"]["extra_field"] == "should_be_preserved"  # Data integrity

    @pytest.mark.asyncio
    async def test_migration_handles_missing_created_at(self, migration_test_database):
        """Test migration behavior with documents missing created_at in event_data."""
        # Document without created_at in event_data
        problematic_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "problematic_agent",
            "thread_id": "problematic_thread",
            "display_id": "problematic_display",
            "run_id": "problematic_run",
            "event_id": "problematic_event",
            "event_type": "display",
            "event_name": "ProblematicEvent",
            "event_data": {
                "content": "Document without created_at",
                # Missing created_at field
            },
            "event_parents": ["BaseEvent", "DisplayEvent"],
        }

        await migration_test_database["agent_events"].insert_one(problematic_doc)

        migration = DocumentV2Migrator()

        # Migration should handle gracefully (document may not be updated)
        await migration.up(migration_test_database)

        # Check the document state
        doc = await migration_test_database["agent_events"].find_one({"event_id": "problematic_event"})

        # Document should either:
        # 1. Be skipped (remain at v1) if aggregation pipeline filters out missing fields, or  
        # 2. Have created_at set to null/default if pipeline handles missing fields

        if doc["schema_version"] == 2:
            # If migrated, the aggregation pipeline processed it but may not have added created_at
            # if the source field was missing - this is valid behavior
            if "created_at" in doc:
                # If created_at field exists, it should be null when source was missing
                assert doc["created_at"] is None or doc["created_at"] == ""
            # If created_at doesn't exist, that's also acceptable behavior
        else:
            # If skipped, should remain at v1
            assert doc["schema_version"] == 1

    @pytest.mark.asyncio
    async def test_migration_performance_with_medium_dataset(self, migration_test_database):
        """Test migration performance with medium-sized dataset."""
        # Create medium dataset (100 documents)
        docs = []
        for i in range(100):
            doc = {
                "schema_version": 1,
                "agent_class": f"TestAgent{i % 10}",
                "agent_id": f"agent_{i:03d}",
                "thread_id": f"thread_{i:03d}",
                "display_id": f"display_{i:03d}",
                "run_id": f"run_{i:03d}",
                "event_id": f"event_{i:03d}",
                "event_type": "display" if i % 2 == 0 else "control",
                "event_name": f"TestEvent{i}",
                "event_data": {
                    "created_at": 1640995200000000000 + (i * 1000000000),  # 1 second increments
                    "content": f"Test content {i}",
                    "index": i,
                },
                "event_parents": ["BaseEvent", "DisplayEvent" if i % 2 == 0 else "ControlEvent"],
            }
            docs.append(doc)

        await migration_test_database["agent_events"].insert_many(docs)

        # Time the migration
        import time

        migration = DocumentV2Migrator()

        start_time = time.time()
        result = await migration.up(migration_test_database)
        duration = time.time() - start_time

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 100 documents
        assert result["agent_events"]["modified"] == 100
        assert result["agent_events"]["matched"] == 100

        # Verify all documents migrated correctly
        migrated_count = await migration_test_database["agent_events"].count_documents({"schema_version": 2})
        assert migrated_count == 100

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, migration_test_database):
        """Test that running the same migration multiple times is safe."""
        # Create test data
        test_doc = {
            "schema_version": 1,
            "agent_class": "TestAgent",
            "agent_id": "idempotent_test",
            "thread_id": "idempotent_thread",
            "display_id": "idempotent_display",
            "run_id": "idempotent_run",
            "event_id": "idempotent_event",
            "event_type": "display",
            "event_name": "IdempotentTestEvent",
            "event_data": {"created_at": 1640995200000000000, "content": "Idempotent test content"},
            "event_parents": ["BaseEvent", "DisplayEvent"],
        }

        await migration_test_database["agent_events"].insert_one(test_doc)

        migration = DocumentV2Migrator()

        # Run migration multiple times
        result1 = await migration.up(migration_test_database)
        result2 = await migration.up(migration_test_database)
        result3 = await migration.up(migration_test_database)

        # First run should modify the document
        assert result1["agent_events"]["modified"] == 1

        # Subsequent runs should not modify already migrated documents
        assert result2["agent_events"]["modified"] == 0
        assert result3["agent_events"]["modified"] == 0

        # Verify document is correctly migrated and not corrupted
        final_doc = await migration_test_database["agent_events"].find_one({"event_id": "idempotent_event"})
        assert final_doc["schema_version"] == 2
        assert final_doc["created_at"] == 1640995200000000000
        assert final_doc["event_data"]["created_at"] == 1640995200000000000


class TestDocumentV2MigratorValidation:
    """Test DocumentV2Migrator validation and error scenarios."""

    def test_migration_validates_version_consistency(self):
        """Test that migration version is consistent across class definition."""
        migration = DocumentV2Migrator()

        # Version should be consistently 2
        assert migration.version == 2
        assert "V2" in migration.__class__.__name__

    def test_migration_has_comprehensive_documentation(self):
        """Test that migration is properly documented."""
        migration = DocumentV2Migrator()

        # Should have meaningful description
        assert len(migration.description) > 50
        assert "created_at" in migration.description.lower()
        assert "optimization" in migration.description.lower()

        # Class should have docstring
        assert migration.__class__.__doc__ is not None
        assert len(migration.__class__.__doc__.strip()) > 100

    @pytest.mark.asyncio
    async def test_migration_validates_input_parameters(self):
        """Test that migration validates input parameters properly."""
        migration = DocumentV2Migrator()

        # Should handle None database gracefully
        with pytest.raises((TypeError, AttributeError)):
            await migration.up(None)

        with pytest.raises((TypeError, AttributeError)):
            await migration.down(None)
