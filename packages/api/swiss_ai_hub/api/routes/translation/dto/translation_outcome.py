from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString


class TranslationOutcome(BaseModel):
    """Service-level result of a translation, kept apart from the HTTP response so internal callers stay HTTP-agnostic."""

    translated: Annotated[
        LocaleString,
        Field(description="The source LocaleString with every successfully translated locale filled in"),
    ]
    failed_locales: Annotated[
        list[str],
        Field(default_factory=list, description="Target locales whose translation failed and kept their prior value"),
    ]
