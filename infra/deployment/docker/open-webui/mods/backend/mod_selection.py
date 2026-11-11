from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ModSelection(BaseModel):
    model_config = ConfigDict(frozen=True)

    mod_id: Annotated[str, Field(min_length=1, max_length=64)]
    publication: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    enabled: bool
    settings: dict[str, JsonValue]
