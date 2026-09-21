from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString


class AccessPresetDTO(BaseModel):
    rule: Annotated[str, Field(description="The access rule string this preset adds.")]
    name: Annotated[str, Field(description="Short, human-readable name for the preset.")]
    description: Annotated[str, Field(description="What this preset grants.")]
    category: Annotated[str, Field(description="Stable category key for grouping in the UI.")]

    @classmethod
    def from_definition(cls, rule: str, i18n_key: str, category: str, t: LocaleHandler) -> Self:
        return cls(
            rule=rule,
            name=t.extract(ApiLocaleString.from_i18n_path(f"api.access.presets.{i18n_key}.name")),
            description=t.extract(ApiLocaleString.from_i18n_path(f"api.access.presets.{i18n_key}.description")),
            category=category,
        )
