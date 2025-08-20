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
        for collection in self.get_affected_collections():
            if collection not in existing_collections:
                logger.warning(f"Collection {collection} does not exist")
                return False

        # Ensures all documents are at the expected starting version
        for collection in self.get_affected_collections():
            count = await db[collection].count_documents({"schema_version": {"$ne": self.version - 1}})
            if count > 0:
                logger.warning(f"Collection {collection} has {count} documents not at version {self.version - 1}")
                return False

        return True
