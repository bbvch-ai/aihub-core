from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString


class TranslationOutcome(BaseModel):
    """Service-level result of a translation.

    Kept apart from the HTTP response so internal callers stay HTTP-agnostic.
    """

    translated: Annotated[
        LocaleString,
        Field(description="The source LocaleString with every empty locale that could be translated filled in"),
    ]
    failed_locales: Annotated[
        list[str],
        Field(default_factory=list, description="Empty locales that could not be translated and stay empty"),
    ]
