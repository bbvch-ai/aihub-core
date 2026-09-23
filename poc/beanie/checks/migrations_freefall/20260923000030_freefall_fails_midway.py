"""A free-fall migration that raises partway, used by check 14b.

Check 14 Q1 found that an `@iterative_migration` which fails partway writes
NOTHING, because Beanie collects its `replace_many` calls and awaits none of them
until the whole collection is transformed (iterative.py:93-128).

`@free_fall_migration` has no such property: `free_fall.py` simply awaits the
author's function, so whatever it writes lands as it goes. This migration writes
document by document and raises on the third of four, so the check can see
exactly what a partial free-fall failure leaves behind.
"""

from beanie import Document, free_fall_migration


class Thing(Document):
    key: str
    state: str

    class Settings:
        name = "freefall_partial"


class FreeFallExploded(RuntimeError):
    """Raised deliberately, so the check cannot mistake it for an infrastructure error."""


class Forward:
    @free_fall_migration(document_models=[Thing])
    async def transform(self, session):
        async for thing in Thing.find_all(session=session):
            if thing.key == "boom":
                raise FreeFallExploded("deliberate failure partway through a free-fall migration")
            thing.state = "migrated"
            await thing.save(session=session)


class Backward:
    @free_fall_migration(document_models=[Thing])
    async def revert(self, session):
        async for thing in Thing.find_all(session=session):
            thing.state = "original"
            await thing.save(session=session)
