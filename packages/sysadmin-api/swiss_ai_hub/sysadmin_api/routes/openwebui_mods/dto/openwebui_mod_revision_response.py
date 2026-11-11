from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, JsonValue, computed_field
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModManifest
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModRevisionEntity


class OpenWebuiModRevisionResponse(BaseModel):
    revision: str
    manifest: OpenWebuiModManifest
    archive_bytes: int
    uploaded_at: datetime
    uploaded_by: str

    @classmethod
    def from_entity(cls, entity: OpenWebuiModRevisionEntity) -> Self:
        return cls(
            revision=entity.revision,
            manifest=OpenWebuiModManifest.model_validate_json(entity.manifest_json),
            archive_bytes=entity.archive_bytes,
            uploaded_at=entity.uploaded_at.replace(tzinfo=UTC),
            uploaded_by=entity.uploaded_by,
        )

    @computed_field
    @property
    def settings_form(self) -> list[dict[str, JsonValue]]:
        return self.manifest.settings_form()
