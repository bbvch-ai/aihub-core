import logging

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from aihub_lib.persistence.base.schema_version import CURRENT_SCHEMA_VERSION
from aihub_lib.persistence.migrations.DocumentMigrator import DocumentMigrator
from aihub_lib.persistence.migrations.v1.DocumentV1Migrator import DocumentV1Migrator
from aihub_lib.persistence.migrations.v2.DocumentV2Migrator import DocumentV2Migrator

logger = logging.getLogger(__name__)

# All migrations registered here in version order
MIGRATIONS: list[type[DocumentMigrator]] = [
    DocumentV1Migrator,
    DocumentV2Migrator,
]


class MigrationOrchestrator:
    """Central migration orchestrator for database schema updates."""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.migrations = sorted(MIGRATIONS, key=lambda m: m.version)

    async def get_current_version(self) -> int:
        """
        Determine the current schema version of the database.

        Returns the lowest schema version found across all user collections.
        """
        # Get all user collections to check schema versions
        all_collections = await self.db.list_collection_names()
        user_collections = [
            collection_name for collection_name in all_collections if not collection_name.startswith("system.")
        ]

        if not user_collections:
            return 0

        min_version = None

        for collection_name in user_collections:
            collection = self.db[collection_name]

            count = await collection.count_documents({}, limit=1)
            if count == 0:
                continue

            pipeline = [
                {"$match": {"schema_version": {"$exists": True}}},
                {"$group": {"_id": None, "min_version": {"$min": "$schema_version"}}},
            ]

            cursor = await collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)

            if result:
                collection_min = result[0]["min_version"]
                min_version = collection_min if min_version is None else min(min_version, collection_min)
            else:
                # Collection has documents but none have schema_version (v0)
                return 0  # Immediately return 0 as it's the minimum possible

        return min_version if min_version is not None else 0

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

    @staticmethod
    async def run_migrations(connection_string: str, db_name: str, target_version: int | None = None) -> None:
        """
        Main entry point for running migrations.

        Connects to MongoDB and runs all pending migrations up to target_version.
        If target_version is None, migrates to the latest version.
        """
        async with AsyncMongoClient(connection_string) as client:
            db = client[db_name]
            orchestrator = MigrationOrchestrator(db)
            await orchestrator.migrate_to(target_version)
