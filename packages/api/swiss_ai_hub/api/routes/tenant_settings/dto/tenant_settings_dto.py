from pydantic import BaseModel, ConfigDict, Field, field_validator
from swiss_ai_hub.core.i18n import LocaleString


class TenantSettingsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_disclaimer: LocaleString = Field(
        description="Plain text below the chat input, up to 400 characters per language. "
        "At least one translation is required."
    )

    @field_validator("chat_disclaimer")
    @classmethod
    def normalize_disclaimer(cls, text: LocaleString) -> LocaleString:
        if not text.has_content():
            raise ValueError("At least one disclaimer translation is required.")
        values = {locale: value.strip() if value else None for locale, value in text.model_dump().items()}
        if any(len(value) > 400 for value in values.values() if value):
            raise ValueError("The disclaimer must be at most 400 characters per language.")
        return LocaleString(**{locale: value or None for locale, value in values.items()})
