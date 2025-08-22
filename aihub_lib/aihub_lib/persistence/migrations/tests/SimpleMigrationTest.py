"""
Simple, real-world migration test framework.

This base class provides a clean, understandable way to test migrations
using actual MongoDB with clear before/after state definitions.
"""

from abc import ABC
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.migrations.DocumentMigrator import DocumentMigrator


class SimpleMigrationTest(ABC):
    """
    Base class for simple, real-world migration testing.

    Tests use actual MongoDB operations with a test database that's
    cleaned up before and after each test. Subclasses just need to
    define the before/after states as class variables and the migration class.
    """

    # Override these in subclasses
    migration_class: type[DocumentMigrator]
    test_db_name = "test_migration_db"

    # Define these as class variables in subclasses
    initial_state: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_up: dict[str, list[dict[str, Any]]] = {}
    expected_state_after_down: dict[str, list[dict[str, Any]]] = {}

    @pytest_asyncio.fixture
    async def db(self):
        """Provide a clean test database for each test."""
        # Use the MongoDB connection from settings
        client = AsyncMongoClient(MongoSettings().CONNECTION_STRING.get_secret_value())

        try:
            # Drop the test database to ensure clean state
            await client.drop_database(self.test_db_name)

            # Get the test database
            db = client[self.test_db_name]

            yield db

        finally:
            # Cleanup after test
            await client.drop_database(self.test_db_name)
            await client.close()

    async def setup_initial_state(self, db: AsyncDatabase) -> None:
        """Insert initial documents into the database."""
        for collection_name, documents in self.initial_state.items():
            if documents:  # Only insert if there are documents
                await db[collection_name].insert_many(documents)

    async def verify_state(self, db: AsyncDatabase, expected_state: dict[str, list[dict[str, Any]]]) -> None:
        """
        Verify the database matches the expected state.

        This compares documents field by field, ignoring _id fields
        since they're auto-generated.
        """
        for collection_name, expected_docs in expected_state.items():
            # Get all documents from collection
            actual_docs = await db[collection_name].find({}).to_list(None)

            # Remove _id fields for comparison
            for doc in actual_docs:
                doc.pop("_id", None)
            for doc in expected_docs:
                doc.pop("_id", None)

            # Sort documents for consistent comparison
            # Sort by the first non-_id key if available
            if expected_docs and actual_docs:
                sort_key = next((k for k in expected_docs[0].keys() if k != "_id"), None)
                if sort_key:
                    expected_docs = sorted(expected_docs, key=lambda d: str(d.get(sort_key, "")))
                    actual_docs = sorted(actual_docs, key=lambda d: str(d.get(sort_key, "")))

            assert len(actual_docs) == len(expected_docs), (
                f"Collection {collection_name}: Expected {len(expected_docs)} documents, "
                f"but found {len(actual_docs)}"
            )

            # Compare each document field by field (to handle datetime precision and field order)
            for i, (expected, actual) in enumerate(zip(expected_docs, actual_docs)):
                # Verify all expected fields are present and have correct values
                for field, expected_value in expected.items():
                    assert field in actual, f"Collection {collection_name}, document {i}: Missing field '{field}'"

                    actual_value = actual[field]

                    # Special handling for datetime fields (MongoDB may change precision and timezone)
                    if isinstance(expected_value, datetime) and isinstance(actual_value, datetime):
                        # Normalize both datetimes to UTC and ignore microsecond precision
                        if expected_value.tzinfo is not None:
                            expected_utc = expected_value.astimezone(UTC)
                        else:
                            expected_utc = expected_value.replace(tzinfo=UTC)

                        if actual_value.tzinfo is not None:
                            actual_utc = actual_value.astimezone(UTC)
                        else:
                            actual_utc = actual_value.replace(tzinfo=UTC)

                        # Compare ignoring microseconds
                        expected_simplified = expected_utc.replace(microsecond=0)
                        actual_simplified = actual_utc.replace(microsecond=0)

                        assert expected_simplified == actual_simplified, (
                            f"Collection {collection_name}, document {i}, field '{field}': "
                            f"Expected {expected_value}, got {actual_value}"
                        )
                    else:
                        assert actual_value == expected_value, (
                            f"Collection {collection_name}, document {i}, field '{field}': "
                            f"Expected {expected_value}, got {actual_value}"
                        )

                # Verify no unexpected fields (allow extra fields that might be added by the system)
                expected_fields = set(expected.keys())
                actual_fields = set(actual.keys())
                unexpected_fields = actual_fields - expected_fields

                # Only flag truly unexpected fields (not common system fields)
                system_fields = {"_id"}  # Add more if needed
                problematic_fields = unexpected_fields - system_fields

                if problematic_fields:
                    print(
                        f"Warning: Collection {collection_name}, document {i} "
                        f"has unexpected fields: {problematic_fields}"
                    )

    @pytest.mark.asyncio
    async def test_migration_up(self, db: AsyncDatabase):
        """Test the UP migration transforms data correctly."""
        # Setup initial state
        await self.setup_initial_state(db)

        # Run migration
        migration = self.migration_class()
        await migration.up(db)

        # Verify final state
        await self.verify_state(db, self.expected_state_after_up)

    @pytest.mark.asyncio
    async def test_migration_down(self, db: AsyncDatabase):
        """Test the DOWN migration (rollback) works correctly."""
        # Setup initial state
        await self.setup_initial_state(db)

        # Run UP migration first
        migration = self.migration_class()
        await migration.up(db)

        # Then run DOWN migration
        await migration.down(db)

        # Verify we're back to expected state after rollback
        await self.verify_state(db, self.expected_state_after_down)

    @pytest.mark.asyncio
    async def test_migration_up_idempotent(self, db: AsyncDatabase):
        """Test that running UP migration twice doesn't cause issues."""
        # Setup initial state
        await self.setup_initial_state(db)

        migration = self.migration_class()

        # Run migration twice
        await migration.up(db)
        await migration.up(db)

        # Should still have the expected state
        await self.verify_state(db, self.expected_state_after_up)

    @pytest.mark.asyncio
    async def test_migration_handles_empty_collections(self, db: AsyncDatabase):
        """Test migration handles empty collections gracefully."""
        # Create empty collections
        for collection_name in self.initial_state.keys():
            await db.create_collection(collection_name)

        migration = self.migration_class()

        # Should not fail on empty collections
        result = await migration.up(db)

        # Verify result indicates no modifications
        for collection_name in self.initial_state.keys():
            if collection_name in result:
                assert result[collection_name].get("modified", 0) == 0

    @pytest.mark.asyncio
    async def test_full_migration_cycle(self, db: AsyncDatabase):
        """Test complete cycle: initial -> up -> down -> up."""
        # Setup initial state
        await self.setup_initial_state(db)

        migration = self.migration_class()

        # First UP
        await migration.up(db)
        await self.verify_state(db, self.expected_state_after_up)

        # DOWN (rollback)
        await migration.down(db)
        await self.verify_state(db, self.expected_state_after_down)

        # UP again
        await migration.up(db)
        await self.verify_state(db, self.expected_state_after_up)
