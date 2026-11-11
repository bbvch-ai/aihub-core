from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aihub_mods.mod_selection import ModSelection


class GlobalModConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(default=0, ge=0)
    mods: list[ModSelection] = Field(default_factory=list, max_length=64)

    @model_validator(mode="after")
    def validate_mods(self) -> Self:
        if len({mod.mod_id for mod in self.mods}) != len(self.mods):
            raise ValueError("Each mod may be selected only once")
        if len(self.model_dump_json().encode()) > 64 * 1024:
            raise ValueError("Global mod configuration exceeds 64 KiB")
        return self
