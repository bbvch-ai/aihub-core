from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a user in the system with their basic information."""

    name: str = Field(..., description="The user's full name", example="John Doe")
    email: str = Field(
        ...,
        description="The user's email address",
        example="john.doe@example.com",
    )
    id: str = Field(
        ..., description="Unique identifier for the user", example="12345678"
    )
    locale: str = Field(
        ..., description="The user's preferred language setting", example="en"
    )

    @staticmethod
    def anonymous(locale: str) -> "User":
        return User(
            name="Anonymous",
            email="anonymous@anonymous.ch",
            id="-1",
            locale=locale,
        )
