from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a user in the system with their basic information."""

    name: str = Field(..., description="The user's full name")
    email: str = Field(
        ...,
        description="The user's email address",
    )
    id: str = Field(
        ...,
        description="Unique identifier for the user",
    )
    locale: str = Field(
        ...,
        description="The user's preferred language setting",
    )

    @staticmethod
    def anonymous(locale: str) -> "User":
        return User(
            name="Anonymous",
            email="anonymous@anonymous.ch",
            id="-1",
            locale=locale,
        )
