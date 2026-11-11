import json
from typing import Annotated, Self

from fastapi import HTTPException
from pydantic import AliasPath, BaseModel, ConfigDict, Field, JsonValue, ValidationError

from aihub_mods.mod_selection import ModSelection


class ModSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    revision: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    tenant_id: Annotated[str, Field(min_length=1, max_length=255)]
    compatibility: dict[str, JsonValue]
    mods: Annotated[list[ModSelection], Field(validation_alias=AliasPath("configuration", "mods"), max_length=64)]

    @classmethod
    def from_response(cls, content: bytes, compatibility: bytes) -> Self:
        try:
            snapshot = cls.model_validate_json(content)
        except ValidationError as error:
            raise HTTPException(502, "Invalid AI Hub mod configuration. Please contact your administrator.") from error
        if snapshot.compatibility != json.loads(compatibility):
            raise HTTPException(
                409, "Mod configuration belongs to another host version. Reload the chat. "
                "If the problem persists, please contact your administrator."
            )
        return snapshot
