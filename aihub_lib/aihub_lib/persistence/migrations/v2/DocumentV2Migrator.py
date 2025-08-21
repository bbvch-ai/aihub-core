"""
Migration to add root-level created_at field for optimized querying.
Schema version: 1 -> 2
"""

import logging
from typing import Any, ClassVar

from pymongo.asynchronous.database import AsyncDatabase

from aihub_lib.persistence.migrations.DocumentMigration import DocumentMigration

logger = logging.getLogger(__name__)


class DocumentV2Migrator(DocumentMigration):
    """
    Migrates all collections to schema_version 2 and adds root-level created_at field to event collections.

    This migration updates ALL collections to schema version 2, but only adds the created_at field
    to event collections for optimized querying by moving the created_at field from nested 
    event_data to the document root level.
    """

    version: ClassVar[int] = 2
    description: ClassVar[str] = "Update all collections to v2 and add root-level created_at field for event collections"
    affected_collections: ClassVar[list[str]] = [
        "agent_events", 
        "process_events",
    ]

    async def migrate_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Apply specific migration logic to event collections: add created_at field AND update schema version.
        """
        collection = db[collection_name]

        # Check if collection is empty
        total_docs = await collection.count_documents({})
        if total_docs == 0:
            logger.info(f"Collection {collection_name} is empty, skipping migration")
            return {"modified": 0, "matched": 0, "skipped": "collection empty"}

        # MongoDB aggregation pipeline ensures atomic update
        # Update docs with v1 or without schema_version (implicit v1)
        result = await collection.update_many(
            {"$or": [{"schema_version": 1}, {"schema_version": {"$exists": False}}]},
            [
                {
                    "$set": {
                        "created_at": "$event_data.created_at",
                        "schema_version": 2,
                    }
                }
            ],
        )

        # Create indices for optimized querying (only if collection has docs)
        if result.matched_count > 0:
            await collection.create_index([("created_at", 1)])
            await collection.create_index([("thread_id", 1), ("created_at", 1)])
            await collection.create_index([("agent_id", 1), ("created_at", 1)])
            await collection.create_index([("thread_id", 1), ("event_type", 1), ("created_at", 1)])

        # Always create schema_version index for version tracking
        await collection.create_index([("schema_version", 1)])

        logger.info(f"Migrated {result.modified_count} documents in {collection_name} to v2 with created_at field")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }

    async def rollback_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Rollback specific migration logic from event collections: remove created_at field AND downgrade schema version.
        """
        collection = db[collection_name]

        result = await collection.update_many(
            {"schema_version": 2},
            {
                "$unset": {"created_at": ""},
                "$set": {"schema_version": 1},
            },
        )

        # Drop indices created during up migration
        try:
            await collection.drop_index([("created_at", 1)])
            await collection.drop_index([("thread_id", 1), ("created_at", 1)])
            await collection.drop_index([("agent_id", 1), ("created_at", 1)])
            await collection.drop_index([("thread_id", 1), ("event_type", 1), ("created_at", 1)])
        except Exception as e:
            logger.warning(f"Could not drop indices: {e}")

        logger.info(f"Rolled back {result.modified_count} documents in {collection_name} to v1, removed created_at field")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }
