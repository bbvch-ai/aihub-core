from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    """Response containing the translated LocaleString with all supported locales populated."""

    translated: Annotated[
        LocaleString,
        Field(description="The LocaleString with translations for all supported locales"),
    ]
