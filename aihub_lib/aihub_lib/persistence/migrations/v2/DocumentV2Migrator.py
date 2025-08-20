"""
Migration to add root-level created_at field for optimized querying.
Schema version: 1 -> 2
"""

import logging
from typing import Any, ClassVar

from pymongo.asynchronous.database import AsyncDatabase

from aihub_lib.persistence.migrations.base import DocumentMigration

logger = logging.getLogger(__name__)


class DocumentV2Migrator(DocumentMigration):
    """
    Migrates all event entities to include root-level created_at field.

    This migration improves query performance by moving the created_at
    field from nested event_data to the document root level.
    """

    version: ClassVar[int] = 2
    description: ClassVar[str] = "Add root-level created_at field for query optimization"

    def get_affected_collections(self) -> list[str]:
        """Collections that need the created_at field migration."""
        return [
            "agent_events",
            "process_events",
        ]

    async def up(self, db: AsyncDatabase) -> dict[str, Any]:
        """Migrate from v1 to v2: Add root-level created_at."""
        stats = {}

        existing_collections = await db.list_collection_names()

        for collection_name in self.get_affected_collections():
            if collection_name not in existing_collections:
                logger.info(f"Collection {collection_name} does not exist, skipping migration")
                stats[collection_name] = {"modified": 0, "matched": 0, "skipped": "collection not exists"}
                continue

            collection = db[collection_name]

            # Check if collection is empty
            total_docs = await collection.count_documents({})
            if total_docs == 0:
                logger.info(f"Collection {collection_name} is empty, skipping migration")
                stats[collection_name] = {"modified": 0, "matched": 0, "skipped": "collection empty"}
                continue

            # MongoDB aggregation pipeline ensures atomic update
            # Update docs without schema_version (implicit v1) or explicit v1
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

            stats[collection_name] = {
                "modified": result.modified_count,
                "matched": result.matched_count,
            }

            # Create indices for optimized querying (only if collection has docs)
            if result.matched_count > 0:
                await collection.create_index([("created_at", 1)])
                await collection.create_index([("thread_id", 1), ("created_at", 1)])
                await collection.create_index([("agent_id", 1), ("created_at", 1)])
                await collection.create_index([("thread_id", 1), ("event_type", 1), ("created_at", 1)])

            # Always create schema_version index for version tracking
            await collection.create_index([("schema_version", 1)])

            logger.info(f"Migrated {result.modified_count} documents in {collection_name} to v2")

        return stats

    async def down(self, db: AsyncDatabase) -> dict[str, Any]:
        """Rollback from v2 to v1: Remove root-level created_at."""
        stats = {}

        for collection_name in self.get_affected_collections():
            collection = db[collection_name]

            result = await collection.update_many(
                {"schema_version": 2},
                {
                    "$unset": {"created_at": ""},
                    "$set": {"schema_version": 1},
                },
            )

            stats[collection_name] = {
                "modified": result.modified_count,
                "matched": result.matched_count,
            }

            # Drop indices created during up migration
            try:
                await collection.drop_index([("created_at", 1)])
                await collection.drop_index([("thread_id", 1), ("created_at", 1)])
                await collection.drop_index([("agent_id", 1), ("created_at", 1)])
                await collection.drop_index([("thread_id", 1), ("event_type", 1), ("created_at", 1)])
            except Exception as e:
                logger.warning(f"Could not drop indices: {e}")

            logger.info(f"Rolled back {result.modified_count} documents in {collection_name} to v1")

        return stats
