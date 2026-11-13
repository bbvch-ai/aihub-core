import json
import re
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class OpenWebuiModManifest(BaseModel):
    """Source entry points shared by package validation, publication and the two runtimes."""

    model_config = ConfigDict(extra="forbid")

    format: Literal[1]
    id: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]
    name: Annotated[str, Field(min_length=1, max_length=100)]
    version: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9.+_-]*$")]
    description: Annotated[str, Field(max_length=2000)] = ""
    bootstrap: str | None = None
    frontend: str | None = None
    backend: str | None = None
    backend_overrides: dict[str, str] = Field(default_factory=dict, max_length=128)
    backend_restart_required: bool = Field(default=False, strict=True)
    replacements: dict[str, str] = Field(default_factory=dict)
    default_settings: dict[str, JsonValue] = Field(default_factory=dict)
    settings_fields: dict[str, dict[str, JsonValue]] = Field(default_factory=dict)

    @property
    def global_only(self) -> bool:
        return self.backend_restart_required or "open_webui.main:lifespan" in self.backend_overrides

    @property
    def supports_global(self) -> bool:
        return bool(self.backend and (self.backend_restart_required or self.backend_overrides))

    @model_validator(mode="after")
    def validate_settings_fields(self) -> Self:
        if len(json.dumps(self.settings_fields, allow_nan=False).encode()) > 16 * 1024:
            raise ValueError("Mod setting field definitions exceed the 16 KiB limit")
        self.settings_form()
        return self

    def settings_form(self) -> list[dict[str, JsonValue]]:
        from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_form import OpenWebuiModForm

        return [
            element.model_dump(mode="json", by_alias=True, exclude_none=True)
            for element in OpenWebuiModForm.build(self.default_settings, self.settings_fields)
        ]

    @field_validator("backend_overrides")
    @classmethod
    def validate_backend_overrides(cls, value: dict[str, str]) -> dict[str, str]:
        for target, handler in value.items():
            if len(target) > 300 or not re.fullmatch(r"open_webui(?:\.[A-Za-z_]\w*)+:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", target):
                raise ValueError(f"Expected a native Open WebUI callable target: {target}")
            if not handler.isidentifier() or len(handler) > 128:
                raise ValueError(f"Expected an exported Python handler name: {handler}")
        return value

    @field_validator("default_settings")
    @classmethod
    def validate_default_settings(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if len(json.dumps(value, allow_nan=False).encode()) > 16 * 1024:
            raise ValueError("Default mod settings exceed the 16 KiB limit")
        return value

    @field_validator("format", mode="before")
    @classmethod
    def validate_format_type(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("The mod format must be a version number")
        return value

    @staticmethod
    def validate_path(value: str) -> str:
        path = PurePosixPath(value)
        if (
            value in {"", "."}
            or len(value) > 240
            or path.is_absolute()
            or path.as_posix() != value
            or any(part in {".", ".."} for part in path.parts)
            or any(character in value for character in "\\:%?#")
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ValueError(f"Expected a normalized relative package path: {value!r}")
        return value

    @field_validator("bootstrap", "frontend", "backend")
    @classmethod
    def validate_entry_path(cls, value: str | None) -> str | None:
        return cls.validate_path(value) if value is not None else None

    @field_validator("replacements")
    @classmethod
    def validate_replacement_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for target, source in value.items():
            cls.validate_path(target)
            cls.validate_path(source)
            if not target.startswith("src/") or not target.endswith(".svelte"):
                raise ValueError(f"Expected an Open WebUI source component path: {target}")
            if not source.endswith(".svelte"):
                raise ValueError(f"Expected a Svelte replacement source file: {source}")
        return value

    @model_validator(mode="after")
    def validate_entry_points(self) -> Self:
        if (self.backend_overrides or self.backend_restart_required) and self.backend is None:
            raise ValueError("Backend overrides and restart requirements need a backend entry")
        if not (self.bootstrap or self.frontend or self.backend or self.replacements):
            raise ValueError("A mod needs a bootstrap entry, frontend entry, component replacement or backend entry")
        for name in ("bootstrap", "frontend"):
            entry = getattr(self, name)
            if entry and not entry.endswith((".js", ".mjs", ".ts")):
                raise ValueError(f"The {name} entry must be a JavaScript or TypeScript file")
        if self.backend and not self.backend.endswith(".py"):
            raise ValueError("The backend entry must be a Python file")
        if self.backend and any(not part.isidentifier() for part in PurePosixPath(self.backend).with_suffix("").parts):
            raise ValueError("The backend entry must be an importable Python module path")
        return self

    @property
    def entry_paths(self) -> set[str]:
        return {path for path in [self.bootstrap, self.frontend, self.backend, *self.replacements.values()] if path is not None}
