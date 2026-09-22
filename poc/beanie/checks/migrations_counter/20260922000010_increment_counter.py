"""A deliberately NON-idempotent migration, used by check 14.

`split_full_name` is a poor probe for double-application: after one run the source
field is gone, so a second run fails on validation and the failure is
indistinguishable from other errors. This one increments instead, so applying it
twice is visible as `applied == 2` rather than as an exception.
"""

from beanie import Document, iterative_migration


class CounterBefore(Document):
    key: str
    applied: int

    class Settings:
        name = "migration_counter"


class CounterAfter(Document):
    key: str
    applied: int

    class Settings:
        name = "migration_counter"


class Forward:
    @iterative_migration()
    async def increment(
        self, input_document: CounterBefore, output_document: CounterAfter
    ) -> None:
        output_document.applied = input_document.applied + 1


class Backward:
    @iterative_migration()
    async def decrement(
        self, input_document: CounterAfter, output_document: CounterBefore
    ) -> None:
        output_document.applied = input_document.applied - 1
