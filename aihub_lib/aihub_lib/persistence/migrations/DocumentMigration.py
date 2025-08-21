"""
Base migration framework for database schema updates.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pymongo.asynchronous.database import AsyncDatabase

logger = logging.getLogger(__name__)


class DocumentMigration(ABC):
    """
    Abstract base class for document migrations.

    Each migration should handle upgrading from version-1 to version
    and downgrading from version to version-1.
    
    The migration pattern ensures ALL collections maintain the same schema_version,
    while allowing specific collections to have additional migration logic.
    """

    version: ClassVar[int]
    description: ClassVar[str]
    affected_collections: ClassVar[list[str]] = []

    def get_affected_collections(self) -> list[str]:
        """
        Return list of collection names that need specific migration logic.
        
        Collections NOT in this list will only receive schema version updates.
        Uses class variable for consistency and validation.
        """
        return self.affected_collections[:]  # Return copy for safety

    async def get_validated_affected_collections(self, db: AsyncDatabase) -> list[str]:
        """
        Get affected collections with validation that they actually exist.
        
        Warns if collections don't exist (could be misspelled collection names).
        Returns only collections that actually exist in the database.
        """
        affected_collections = self.get_affected_collections()
        if not affected_collections:
            return []

        existing_collections = await db.list_collection_names()
        validated_collections = []

        for collection_name in affected_collections:
            if collection_name in existing_collections:
                validated_collections.append(collection_name)
            else:
                logger.warning(
                    f"⚠️  Collection '{collection_name}' specified in migration v{self.version} "
                    f"does not exist in database. This could be a misspelled collection name. "
                    f"Available collections: {sorted(existing_collections)}"
                )

        return validated_collections

    @abstractmethod
    async def migrate_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Apply specific migration logic to an affected collection.
        
        This method should handle both the specific changes AND schema version update.
        """
        pass

    @abstractmethod
    async def rollback_collection(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """
        Rollback specific migration logic from an affected collection.
        
        This method should handle both the specific rollback AND schema version downgrade.
        """
        pass

    async def get_user_collections(self, db: AsyncDatabase) -> list[str]:
        """Get all user collections (excluding system collections)."""
        all_collections = await db.list_collection_names()
        return [
            collection_name for collection_name in all_collections 
            if not collection_name.startswith('system.')
        ]

    async def update_schema_version_only(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Update only the schema version for collections without specific migration logic."""
        collection = db[collection_name]

        # Check if collection is empty
        total_docs = await collection.count_documents({})
        if total_docs == 0:
            logger.info(f"Collection {collection_name} is empty, skipping schema version update")
            return {"modified": 0, "matched": 0, "skipped": "collection empty"}

        # Update schema version from previous version to current version
        result = await collection.update_many(
            {"$or": [{"schema_version": self.version - 1}, {"schema_version": {"$exists": False}}]},
            {"$set": {"schema_version": self.version}},
        )

        # Create schema_version index for version tracking
        await collection.create_index([("schema_version", 1)])

        logger.info(f"Updated schema version for {result.modified_count} documents in {collection_name} to v{self.version}")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }

    async def downgrade_schema_version_only(self, db: AsyncDatabase, collection_name: str) -> dict[str, Any]:
        """Downgrade only the schema version for collections without specific rollback logic."""
        collection = db[collection_name]

        result = await collection.update_many(
            {"schema_version": self.version},
            {"$set": {"schema_version": self.version - 1}},
        )

        logger.info(f"Downgraded schema version for {result.modified_count} documents in {collection_name} to v{self.version - 1}")

        return {
            "modified": result.modified_count,
            "matched": result.matched_count,
        }

    async def up(self, db: AsyncDatabase) -> dict[str, Any]:
        """
        Migrate from version-1 to version.

        Returns dictionary with migration statistics.
        """
        stats = {}
        
        user_collections = await self.get_user_collections(db)
        validated_affected_collections = await self.get_validated_affected_collections(db)
        
        logger.info(f"Processing {len(user_collections)} collections for v{self.version} migration")
        logger.info(f"Collections with specific migration logic: {validated_affected_collections}")

        for collection_name in user_collections:
            if collection_name in validated_affected_collections:
                # Collections with specific migration logic
                stats[collection_name] = await self.migrate_collection(db, collection_name)
            else:
                # Collections that only need schema version update
                stats[collection_name] = await self.update_schema_version_only(db, collection_name)

        return stats

    async def down(self, db: AsyncDatabase) -> dict[str, Any]:
        """
        Rollback from version to version-1.

        Returns dictionary with rollback statistics.
        """
        stats = {}
        
        user_collections = await self.get_user_collections(db)
        validated_affected_collections = await self.get_validated_affected_collections(db)
        
        logger.info(f"Processing {len(user_collections)} collections for v{self.version} rollback")
        logger.info(f"Collections with specific rollback logic: {validated_affected_collections}")

        for collection_name in user_collections:
            if collection_name in validated_affected_collections:
                # Collections with specific rollback logic
                stats[collection_name] = await self.rollback_collection(db, collection_name)
            else:
                # Collections that only need schema version downgrade
                stats[collection_name] = await self.downgrade_schema_version_only(db, collection_name)

        return stats

    async def validate_prerequisites(self, db: AsyncDatabase) -> bool:
        """
        Validate that the database is in the correct state for this migration.

        Returns True if migration can proceed, False otherwise.
        """
        existing_collections = await db.list_collection_names()

        # Check each affected collection
        for collection in self.get_affected_collections():
            if collection not in existing_collections:
                # Collection doesn't exist - this is fine for new/empty databases
                logger.info(f"Collection {collection} does not exist, skipping migration")
                continue

            # Collection exists - check if any documents are at wrong version
            total_docs = await db[collection].count_documents({})
            if total_docs == 0:
                # Empty collection - this is fine
                logger.info(f"Collection {collection} is empty, skipping migration")
                continue

            # Check for documents without schema_version (v1 implicit)
            docs_without_version = await db[collection].count_documents({"schema_version": {"$exists": False}})
            docs_with_target_version = await db[collection].count_documents({"schema_version": self.version - 1})
            docs_at_higher_version = await db[collection].count_documents({"schema_version": {"$gt": self.version - 1}})

            # If we have documents at higher version, migration already applied
            if docs_at_higher_version > 0:
                logger.info(
                    f"Collection {collection} already has {docs_at_higher_version} "
                    f"documents at version >= {self.version}"
                )
                continue

            # If we have documents without version or at target version, we can proceed
            if docs_without_version > 0 or docs_with_target_version > 0:
                continue

            # If we have docs at other versions, fail
            docs_at_other_versions = (
                total_docs - docs_without_version - docs_with_target_version - docs_at_higher_version
            )
            if docs_at_other_versions > 0:
                logger.warning(f"Collection {collection} has {docs_at_other_versions} documents at unexpected versions")
                return False

        return True
