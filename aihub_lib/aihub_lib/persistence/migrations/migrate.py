"""
Central migration orchestrator for database schema updates.
"""

import logging

from pymongo import MongoClient
from pymongo.database import Database

from aihub_lib.persistence.base.schema_version import CURRENT_SCHEMA_VERSION
from aihub_lib.persistence.migrations.base import DocumentMigration
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator

logger = logging.getLogger(__name__)

# All migrations registered here in version order
MIGRATIONS: list[type[DocumentMigration]] = [
    DocumentV2Migrator,
]


class MigrationOrchestrator:
    """Orchestrates database migrations."""

    def __init__(self, db: Database):
        self.db = db
        self.migrations = sorted(MIGRATIONS, key=lambda m: m.version)

    async def get_current_version(self) -> int:
        """
        Determine the current schema version of the database.

        Returns the lowest schema version found across all collections.
        """
        min_version = CURRENT_SCHEMA_VERSION

        for migration_class in self.migrations:
            migration = migration_class()
            for collection_name in migration.get_affected_collections():
                doc = await self.db[collection_name].find_one({}, {"schema_version": 1})
                if doc and "schema_version" in doc:
                    min_version = min(min_version, doc["schema_version"])
                elif doc:
                    # Document exists but no version means v1
                    min_version = 1

        return min_version

    async def migrate_to(self, target_version: int | None = None) -> None:
        """
        Migrate database to target version.

        If target_version is None, migrates to latest version.
        """
        if target_version is None:
            target_version = CURRENT_SCHEMA_VERSION

        current_version = await self.get_current_version()

        if current_version == target_version:
            logger.info(f"Database already at version {target_version}")
            return

        if current_version < target_version:
            await self._migrate_up(current_version, target_version)
        else:
            await self._migrate_down(current_version, target_version)

    async def _migrate_up(self, from_version: int, to_version: int) -> None:
        """Apply migrations to upgrade schema."""
        logger.info(f"Upgrading database from v{from_version} to v{to_version}")

        for migration_class in self.migrations:
            if from_version < migration_class.version <= to_version:
                migration = migration_class()

                logger.info(f"Applying migration v{migration.version}: {migration.description}")

                if not await migration.validate_prerequisites(self.db):
                    raise RuntimeError(f"Prerequisites not met for migration v{migration.version}")

                stats = await migration.up(self.db)

                logger.info(f"Successfully applied migration v{migration.version}: {stats}")

                from_version = migration.version

    async def _migrate_down(self, from_version: int, to_version: int) -> None:
        """Apply migrations to downgrade schema."""
        logger.info(f"Downgrading database from v{from_version} to v{to_version}")

        # Apply in reverse order for rollback
        for migration_class in reversed(self.migrations):
            if to_version < migration_class.version <= from_version:
                migration = migration_class()

                logger.info(f"Rolling back migration v{migration.version}: {migration.description}")

                stats = await migration.down(self.db)

                logger.info(f"Successfully rolled back migration v{migration.version}: {stats}")


async def run_migrations(connection_string: str, db_name: str, target_version: int | None = None) -> None:
    """
    Main entry point for running migrations.

    Connects to MongoDB and runs all pending migrations up to target_version.
    If target_version is None, migrates to the latest version.
    """
    client = MongoClient(connection_string)
    db = client[db_name]

    try:
        orchestrator = MigrationOrchestrator(db)
        await orchestrator.migrate_to(target_version)
    finally:
        client.close()
