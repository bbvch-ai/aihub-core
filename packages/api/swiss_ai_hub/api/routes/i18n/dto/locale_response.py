from typing import Annotated

from pydantic import BaseModel, Field


class LocaleResponse(BaseModel):
    """Represents language and test information for a locale."""

    lang: Annotated[str, Field(description="The language code for the locale", example="en")]
    test: Annotated[
        str,
        Field(
            description="Test string in the specified language",
            example="Your language is set to English.",
        ),
    ]
