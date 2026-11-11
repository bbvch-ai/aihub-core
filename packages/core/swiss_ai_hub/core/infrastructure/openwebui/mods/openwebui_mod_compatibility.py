from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class OpenWebuiModCompatibility(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    openwebui: Annotated[str, Field(min_length=1, max_length=64)]
    source_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    svelte: Annotated[str, Field(min_length=1, max_length=64)]
    host_protocol: Annotated[int, Field(ge=1)]
    python: Annotated[str, Field(pattern=r"^3\.\d+$")]
