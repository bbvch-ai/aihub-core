import hashlib
import json
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModCompatibility, OpenWebuiModResolvedConfiguration


class OpenWebuiModRuntimeConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    compatibility: OpenWebuiModCompatibility
    configuration: OpenWebuiModResolvedConfiguration
    revision: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]

    @classmethod
    def from_configuration(
        cls, tenant_id: str, compatibility: OpenWebuiModCompatibility, configuration: OpenWebuiModResolvedConfiguration,
    ) -> Self:
        content = json.dumps({
            "tenant_id": tenant_id,
            "compatibility": compatibility.model_dump(mode="json"),
            "mods": [mod.model_dump(mode="json") for mod in configuration.mods],
        }, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        return cls(
            tenant_id=tenant_id, compatibility=compatibility, configuration=configuration,
            revision=hashlib.sha256(content).hexdigest(),
        )
