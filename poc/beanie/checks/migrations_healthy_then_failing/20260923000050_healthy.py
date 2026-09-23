"""Migration A — healthy, reversible. First half of check 15 T2.

Runs to completion and is recorded in `migrations_log`. Its Backward is correct,
which is what makes T2's result unambiguous: if a backward run reverts this, it
reverted the wrong migration.
"""

from beanie import Document, iterative_migration


class BeforeA(Document):
    key: str
    state: str

    class Settings:
        name = "backward_t2"


class AfterA(Document):
    key: str
    state: str

    class Settings:
        name = "backward_t2"


class Forward:
    @iterative_migration()
    async def apply_a(self, input_document: BeforeA, output_document: AfterA) -> None:
        output_document.state = "after-A"


class Backward:
    @iterative_migration()
    async def undo_a(self, input_document: AfterA, output_document: BeforeA) -> None:
        output_document.state = "original"
