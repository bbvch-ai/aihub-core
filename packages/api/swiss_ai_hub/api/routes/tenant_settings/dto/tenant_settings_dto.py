from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.i18n import LocaleString


class TenantSettingsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_disclaimer: LocaleString = Field(description="Chat disclaimer in each supported language.")
