"""
Migration to add schema_version field to all documents.
Schema version: 0 -> 1
"""

import logging
from typing import Any, ClassVar

from pymongo.asynchronous.database import AsyncDatabase

from aihub_lib.persistence.migrations.DocumentMigration import DocumentMigration

logger = logging.getLogger(__name__)


class DocumentV1Migrator(DocumentMigration):
    """
    Migrates all documents in all collections to include schema_version field set to 1.

    This migration is the initial migration that brings all existing
    documents without a schema_version field to version 1. Since this only
    adds schema_version (no specific collection logic), all collections
    are handled uniformly by the base class.
    """

    version: ClassVar[int] = 1
    description: ClassVar[str] = "Add schema_version field to all documents in all collections"
    affected_collections: ClassVar[list[str]] = []  # No specific collection logic needed

    async def migrate_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Not used for V1 migration since no collections have specific logic.
        All collections are handled by update_schema_version_only().
        """
        raise NotImplementedError("V1 migration has no collections with specific logic")

    async def rollback_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Not used for V1 migration since no collections have specific logic.
        All collections are handled by downgrade_schema_version_only().
        """
        raise NotImplementedError("V1 migration has no collections with specific rollback logic")

    async def update_schema_version_only(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Override to handle V0 -> V1 transition (documents without schema_version field).
        """
        collection = db[collection_name]

        # Check if collection is empty
        total_docs = await collection.count_documents({})
        if total_docs == 0:
            logger.info(f"Collection {collection_name} is empty, skipping migration")
            return {"modified": 0, "matched": 0, "skipped": "collection empty"}

        # For V1, we need to handle documents without schema_version field (implicit v0)
        result = await collection.update_many(
            {"schema_version": {"$exists": False}},
            {"$set": {"schema_version": 1}},
        )

        # Create schema_version index for version tracking
        await collection.create_index([("schema_version", 1)])

        logger.info(f"Migrated {result.modified_count} documents in {collection_name} to v1")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }

    async def downgrade_schema_version_only(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Override to handle V1 -> V0 transition (remove schema_version field entirely).
        """
        collection = db[collection_name]

        result = await collection.update_many(
            {"schema_version": 1},
            {"$unset": {"schema_version": ""}},
        )

        # Drop schema_version index created during up migration
        try:
            await collection.drop_index([("schema_version", 1)])
        except Exception as e:
            logger.warning(f"Could not drop schema_version index: {e}")

        logger.info(f"Rolled back {result.modified_count} documents in {collection_name} to v0")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }