"""A migration that raises partway through, used by check 14.

FerretDB has no transactions (check 13), so a migration that fails halfway cannot
roll back. This one fails deterministically on the document whose key is "boom",
with documents before and after it in the collection, so the check can see exactly
what a partial application leaves behind.
"""

from beanie import Document, iterative_migration


class Before(Document):
    key: str
    state: str

    class Settings:
        name = "migration_partial"


class After(Document):
    key: str
    state: str

    class Settings:
        name = "migration_partial"


class MigrationExploded(RuntimeError):
    """Raised deliberately, so the check cannot mistake it for an infrastructure error."""


class Forward:
    @iterative_migration()
    async def transform(self, input_document: Before, output_document: After) -> None:
        if input_document.key == "boom":
            raise MigrationExploded("deliberate failure partway through the migration")
        output_document.state = "migrated"
