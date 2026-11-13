import json
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class OpenWebuiModSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mod_id: Annotated[str, Field(max_length=64, pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]
    enabled: bool = True
    settings: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_settings(self) -> Self:
        if len(json.dumps(self.settings, allow_nan=False).encode()) > 16 * 1024:
            raise ValueError("Mod settings exceed the 16 KiB limit")
        return self
