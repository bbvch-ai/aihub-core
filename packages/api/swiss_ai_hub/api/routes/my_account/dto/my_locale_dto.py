from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler


class MyLocaleDTO(BaseModel):
    """The UI language the user wants persisted against their account."""

    locale: Annotated[
        str,
        Field(
            description=f"ISO 639-1 language code, one of: {', '.join(LocaleHandler.LOCALE_WHITE_LIST)}.",
            examples=["en"],
        ),
    ]
