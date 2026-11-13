from datetime import UTC, datetime
from typing import Self

from mongoengine import DateTimeField, Document, IntField, StringField

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication


class OpenWebuiModEntity(Document):
    meta = {"collection": "openwebui_mods", "indexes": ["publication"]}

    mod_id = StringField(primary_key=True)
    source_revision = StringField(required=True)
    publication = StringField(required=True)
    manifest_json = StringField(required=True)
    publication_manifest_json = StringField(required=True)
    installed_at = DateTimeField(required=True)
    archive_bytes = IntField(required=True)
    installed_by = StringField(required=True)

    @classmethod
    def install(cls, source: OpenWebuiModPackage, publication: OpenWebuiModPublication, installed_by: str, archive_bytes: int) -> Self:
        return cls.objects(mod_id=source.manifest.id).modify(
            upsert=True, new=True,
            set__source_revision=source.revision,
            set__publication=publication.revision, set__archive_bytes=archive_bytes,
            set__manifest_json=source.manifest.model_dump_json(),
            set__publication_manifest_json=publication.manifest.model_dump_json(),
            set__installed_at=datetime.now(UTC), set__installed_by=installed_by,
        )

    @classmethod
    def find_mod(cls, mod_id: str) -> Self | None:
        return cls.objects(mod_id=mod_id).first()

    @classmethod
    def find_publication(cls, revision: str) -> Self | None:
        return cls.objects(publication=revision).first()

    @classmethod
    def installed(cls) -> list[Self]:
        return list(cls.objects.order_by("mod_id"))
