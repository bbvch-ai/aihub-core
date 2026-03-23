from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString


class TranslationResponse(BaseModel):
    """Response containing the translated LocaleString with all supported locales populated."""

    translated: Annotated[
        LocaleString,
        Field(description="The LocaleString with translations for all supported locales"),
    ]
