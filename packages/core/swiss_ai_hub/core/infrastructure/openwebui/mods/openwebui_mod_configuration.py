import json
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection import OpenWebuiModSelection


class OpenWebuiModConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    version: Annotated[int, Field(ge=0)] = 0
    mods: Annotated[list[OpenWebuiModSelection], Field(max_length=64)] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_mods(self) -> Self:
        if len({mod.mod_id for mod in self.mods}) != len(self.mods):
            raise ValueError("Each mod can be selected only once per tenant")
        if len(json.dumps([mod.model_dump() for mod in self.mods], allow_nan=False).encode()) > 64 * 1024:
            raise ValueError("Tenant mod configuration exceeds the 64 KiB limit")
        return self
