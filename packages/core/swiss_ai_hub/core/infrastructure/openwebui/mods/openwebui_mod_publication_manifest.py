from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest


class OpenWebuiModPublicationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    format: Literal[1]
    source_revision: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    compatibility: OpenWebuiModCompatibility
    bootstrap: str | None = None
    frontend: str | None = None
    replacements: dict[str, str] = Field(default_factory=dict)
    backend_targets: dict[str, dict[str, JsonValue]] = Field(default_factory=dict, max_length=128)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("format", mode="before")
    @classmethod
    def validate_format(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Publication format must be a version number")
        return value

    @field_validator("bootstrap", "frontend")
    @classmethod
    def validate_frontend(cls, value: str | None) -> str | None:
        if value is not None:
            OpenWebuiModManifest.validate_path(value)
            if not value.endswith(".mjs"):
                raise ValueError("Published frontend entries must be ES modules")
        return value

    @field_validator("replacements")
    @classmethod
    def validate_replacements(cls, value: dict[str, str]) -> dict[str, str]:
        for target, source in value.items():
            OpenWebuiModManifest.validate_path(target)
            cls.validate_frontend(source)
        return value
