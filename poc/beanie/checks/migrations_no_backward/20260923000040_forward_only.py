"""A migration with a Forward class and no Backward, used by check 15 T1.

Beanie's runner takes `backward_class` as optional (`runner.py:27`), and
`run_backward` moves the log pointer whether or not one exists. This file is the
omission, written deliberately.
"""

from beanie import Document, iterative_migration


class Before(Document):
    key: str
    state: str

    class Settings:
        name = "backward_t1"


class After(Document):
    key: str
    state: str

    class Settings:
        name = "backward_t1"


class Forward:
    @iterative_migration()
    async def transform(self, input_document: Before, output_document: After) -> None:
        output_document.state = "migrated"


# No Backward class. That is the point of the check.
