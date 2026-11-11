from datetime import UTC, datetime
from typing import Self

from mongoengine import DateTimeField, Document, IntField, StringField

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage


class OpenWebuiModRevisionEntity(Document):
    meta = {
        "collection": "openwebui_mod_revisions",
        "indexes": ["mod_id", "-uploaded_at", ("mod_id", "-uploaded_at", "revision")],
    }

    revision = StringField(primary_key=True, regex=r"^[a-f0-9]{64}$")
    mod_id = StringField(required=True)
    # Component source paths contain dots, which cannot be MongoEngine DictField keys.
    manifest_json = StringField(required=True)
    archive_bytes = IntField(required=True)
    uploaded_at = DateTimeField(required=True)
    uploaded_by = StringField(required=True)

    @classmethod
    def record_upload(cls, package: OpenWebuiModPackage, archive_bytes: int, uploaded_by: str) -> Self:
        return cls.objects(revision=package.revision).modify(
            upsert=True,
            new=True,
            set_on_insert__mod_id=package.manifest.id,
            set_on_insert__manifest_json=package.manifest.model_dump_json(),
            set_on_insert__archive_bytes=archive_bytes,
            set_on_insert__uploaded_at=datetime.now(UTC),
            set_on_insert__uploaded_by=uploaded_by,
        )

    @classmethod
    def find_revision(cls, revision: str) -> Self | None:
        return cls.objects(revision=revision).first()

    @classmethod
    def list_revisions(cls, mod_id: str | None, offset: int, limit: int) -> list[Self]:
        query = cls.objects(mod_id=mod_id) if mod_id else cls.objects
        return list(query.order_by("-uploaded_at", "revision").skip(offset).limit(limit))

    @classmethod
    def list_mod_ids(cls) -> list[str]:
        return cls.objects.distinct("mod_id")

    @classmethod
    def latest_revision(cls, mod_id: str) -> Self | None:
        return cls.objects(mod_id=mod_id).order_by("-uploaded_at", "revision").first()
