"""Migration 3 of a three-migration chain, used by check 15 T3.

Each step increments `applied`, so after three forward runs the value is 3 and a
backward run that undoes everything leaves 0. That makes "distance=0 means without
limit" visible as a number rather than as an absence.
"""

from beanie import Document, iterative_migration


class Counter3Before(Document):
    key: str
    applied: int

    class Settings:
        name = "backward_t3"


class Counter3After(Document):
    key: str
    applied: int

    class Settings:
        name = "backward_t3"


class Forward:
    @iterative_migration()
    async def step_up(self, input_document: Counter3Before, output_document: Counter3After) -> None:
        output_document.applied = input_document.applied + 1


class Backward:
    @iterative_migration()
    async def step_down(self, input_document: Counter3After, output_document: Counter3Before) -> None:
        output_document.applied = input_document.applied - 1