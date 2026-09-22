"""A real Beanie iterative migration, used by check 13.

Models a shape change of the kind the platform actually accumulates: one field
becomes two. Written in Beanie's own migration format so the check exercises the
framework rather than a simulation of it.
"""

from pydantic import BaseModel

from beanie import Document, free_fall_migration, iterative_migration


class OldPerson(Document):
    full_name: str
    tenant: str

    class Settings:
        name = "migration_people"


class NewPerson(Document):
    first_name: str
    last_name: str
    tenant: str

    class Settings:
        name = "migration_people"


class Forward:
    @iterative_migration()
    async def split_full_name(
        self, input_document: OldPerson, output_document: NewPerson
    ) -> None:
        parts = input_document.full_name.split(" ", 1)
        output_document.first_name = parts[0]
        output_document.last_name = parts[1] if len(parts) > 1 else ""


class Backward:
    @iterative_migration()
    async def join_name(
        self, input_document: NewPerson, output_document: OldPerson
    ) -> None:
        output_document.full_name = f"{input_document.first_name} {input_document.last_name}".strip()
