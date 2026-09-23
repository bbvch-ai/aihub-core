"""Migration B — raises, so it never reaches `migrations_log`. Second half of check 15 T2.

Written as a free-fall migration so it genuinely writes before it fails (check 14b):
an iterative one would write nothing, and T2 needs partial state to exist in order
to show that a backward run does not clean it up.
"""

from beanie import Document, free_fall_migration


class ThingB(Document):
    key: str
    state: str

    class Settings:
        name = "backward_t2"


class MigrationBExploded(RuntimeError):
    """Raised deliberately, so the check cannot mistake it for an infrastructure error."""


class Forward:
    @free_fall_migration(document_models=[ThingB])
    async def apply_b(self, session):
        async for thing in ThingB.find_all(session=session):
            if thing.key == "row-2":
                raise MigrationBExploded("migration B fails after writing row-0 and row-1")
            thing.state = "after-B"
            await thing.save(session=session)


class Backward:
    @free_fall_migration(document_models=[ThingB])
    async def undo_b(self, session):
        async for thing in ThingB.find_all(session=session):
            thing.state = "after-A"
            await thing.save(session=session)
