from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, JsonValue, computed_field
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModManifest, OpenWebuiModPublicationManifest
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity


class OpenWebuiModCatalogEntry(BaseModel):
    source_revision: str
    manifest: OpenWebuiModManifest
    builtin: bool
    installed_at: datetime
    warnings: list[str]

    @classmethod
    def from_entity(cls, entity: OpenWebuiModEntity, *, builtin: bool) -> Self:
        return cls(
            source_revision=entity.source_revision,
            manifest=OpenWebuiModManifest.model_validate_json(entity.manifest_json),
            builtin=builtin,
            installed_at=entity.installed_at.replace(tzinfo=UTC),
            warnings=OpenWebuiModPublicationManifest.model_validate_json(entity.publication_manifest_json).warnings,
        )

    @computed_field
    @property
    def settings_form(self) -> list[dict[str, JsonValue]]:
        return self.manifest.settings_form()

    @computed_field
    @property
    def scopes(self) -> list[Literal["tenant", "global"]]:
        scopes: list[Literal["tenant", "global"]] = []
        if not self.manifest.global_only:
            scopes.append("tenant")
        if self.manifest.supports_global:
            scopes.append("global")
        return scopes
