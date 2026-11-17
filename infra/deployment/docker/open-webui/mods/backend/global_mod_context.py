from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class GlobalModContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    scope: Literal["global"] = "global"
    id: str
    mod_id: str
    publication: str
    settings: dict[str, JsonValue]
    app: Any
    request: Any = None
    tenant_id: None = None
    user: None = None
    state: dict[str, Any] = Field(default_factory=dict)
