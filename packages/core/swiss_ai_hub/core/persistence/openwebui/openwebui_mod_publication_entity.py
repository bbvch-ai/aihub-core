from datetime import UTC, datetime
from typing import Self

from mongoengine import DateTimeField, Document, IntField, StringField

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication


class OpenWebuiModPublicationEntity(Document):
    meta = {
        "collection": "openwebui_mod_publications",
        "indexes": ["mod_id", "source_revision", "-published_at"],
    }

    revision = StringField(primary_key=True, regex=r"^[a-f0-9]{64}$")
    mod_id = StringField(required=True)
    source_revision = StringField(required=True)
    manifest_json = StringField(required=True)
    archive_bytes = IntField(required=True)
    published_at = DateTimeField(required=True)
    published_by = StringField(required=True)

    @classmethod
    def record_publication(
        cls, publication: OpenWebuiModPublication, mod_id: str, archive_bytes: int, published_by: str
    ) -> Self:
        return cls.objects(revision=publication.revision).modify(
            upsert=True,
            new=True,
            set_on_insert__mod_id=mod_id,
            set_on_insert__source_revision=publication.manifest.source_revision,
            set_on_insert__manifest_json=publication.manifest.model_dump_json(),
            set_on_insert__archive_bytes=archive_bytes,
            set_on_insert__published_at=datetime.now(UTC),
            set_on_insert__published_by=published_by,
        )

    @classmethod
    def find_publication(cls, revision: str) -> Self | None:
        return cls.objects(revision=revision).first()

    @classmethod
    def list_publications(cls, source_revision: str) -> list[Self]:
        return list(cls.objects(source_revision=source_revision).order_by("-published_at", "revision"))
