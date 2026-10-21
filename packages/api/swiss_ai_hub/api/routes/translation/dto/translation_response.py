from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.routes.translation.dto.translation_outcome import TranslationOutcome


class TranslationResponse(BaseModel):
    """Response containing the translated LocaleString and the locales that could not be translated."""

    translated: Annotated[
        LocaleString,
        Field(description="The LocaleString with every empty locale that could be translated filled in"),
    ]
    failed_locales: Annotated[
        list[str],
        Field(default_factory=list, description="Empty locales that could not be translated and stay empty"),
    ]

    @classmethod
    def from_outcome(cls, outcome: TranslationOutcome) -> Self:
        return cls(translated=outcome.translated, failed_locales=outcome.failed_locales)
