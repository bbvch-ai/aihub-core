from typing import Any

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ModRequestContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: str
    tenant_id: str
    mod_id: str
    publication: str
    settings: dict[str, JsonValue]
    request: Request
    user: dict[str, Any]
    path: str = ""
    state: dict[str, Any] = Field(default_factory=dict)
