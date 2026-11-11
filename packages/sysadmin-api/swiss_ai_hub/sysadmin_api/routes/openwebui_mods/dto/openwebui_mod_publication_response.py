from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModPublicationManifest
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModPublicationEntity


class OpenWebuiModPublicationResponse(BaseModel):
    revision: str
    mod_id: str
    manifest: OpenWebuiModPublicationManifest
    archive_bytes: int
    published_at: datetime
    published_by: str

    @classmethod
    def from_entity(cls, entity: OpenWebuiModPublicationEntity) -> Self:
        return cls(
            revision=entity.revision,
            mod_id=entity.mod_id,
            manifest=OpenWebuiModPublicationManifest.model_validate_json(entity.manifest_json),
            archive_bytes=entity.archive_bytes,
            published_at=entity.published_at.replace(tzinfo=UTC),
            published_by=entity.published_by,
        )
