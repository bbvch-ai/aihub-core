import asyncio
from typing import Self

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest


class OpenWebuiModHost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compatibility: OpenWebuiModCompatibility
    components: set[str]
    callables: dict[str, dict[str, JsonValue]] = Field(default_factory=dict)

    @field_validator("components")
    @classmethod
    def validate_components(cls, value: set[str]) -> set[str]:
        for path in value:
            OpenWebuiModManifest.validate_path(path)
            if not path.startswith("src/") or not path.endswith(".svelte"):
                raise ValueError(f"Invalid host component ID: {path}")
        return value

    @classmethod
    async def load(cls, base_url: str) -> Self:
        async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=15) as client:
            contract, catalog, callables = await asyncio.gather(
                client.get("/_aihub/mods/compatibility.json"),
                client.get("/_aihub/mods/components.json"),
                client.get("/_aihub/mods/callables.json"),
            )
        for response in (contract, catalog, callables):
            response.raise_for_status()
            if response.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                raise ValueError("Open WebUI did not return the mod host contract")
        return cls(compatibility=contract.json(), components=catalog.json(), callables=callables.json())
