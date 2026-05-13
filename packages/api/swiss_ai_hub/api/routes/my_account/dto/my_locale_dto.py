from typing import Annotated

from pydantic import BaseModel, Field


class MyLocaleDTO(BaseModel):
    locale: Annotated[str, Field(description="ISO 639-1 language code: one of 'de', 'en', 'fr', 'it'.")]
