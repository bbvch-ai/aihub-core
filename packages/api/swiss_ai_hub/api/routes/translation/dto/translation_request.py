from typing import Annotated, Literal

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString


class TranslationRequest(BaseModel):
    """Request body for translating a LocaleString to all supported locales."""

    text: Annotated[
        LocaleString,
        Field(description="The LocaleString containing the source text to translate"),
    ]
    source_locale: Annotated[
        Literal["de", "en", "fr", "it"],
        Field(default="en", description="The source locale to translate from"),
    ] = "en"
    model_name: Annotated[
        str | None,
        Field(default=None, description="Optional LLM model name to use for translation"),
    ] = None
