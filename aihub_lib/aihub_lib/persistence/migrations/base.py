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
    """

    version: ClassVar[int]
    description: ClassVar[str]

    @abstractmethod
    async def up(self, db: AsyncDatabase) -> dict[str, Any]:
        """
        Migrate from version-1 to version.

        Returns dictionary with migration statistics.
        """
        pass

    @abstractmethod
    async def down(self, db: AsyncDatabase) -> dict[str, Any]:
        """
        Rollback from version to version-1.

        Returns dictionary with rollback statistics.
        """
        pass

    @abstractmethod
    def get_affected_collections(self) -> list[str]:
        """Return list of collection names this migration affects."""
        pass

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
