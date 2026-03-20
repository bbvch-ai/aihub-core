from typing import Annotated, Self

from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a user in the system with their basic information."""

    name: Annotated[str, Field(description="The user's full name")]
    email: Annotated[
        str,
        Field(
            description="The user's email address",
        ),
    ]
    id: Annotated[
        str,
        Field(
            description="Unique identifier for the user",
        ),
    ]
    locale: Annotated[
        str,
        Field(
            description="The user's preferred language setting",
        ),
    ]

    @staticmethod
    def anonymous(locale: str) -> Self:
        return User(
            name="Anonymous",
            email="anonymous@anonymous.ch",
            id="-1",
            locale=locale,
        )
