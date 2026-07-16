import re
from typing import Self

from bson import ObjectId
from mongoengine import BooleanField, Document, EmbeddedDocumentField, StringField, ValidationError
from mongoengine.context_managers import switch_db

from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


class BucketEntity(Document):
    """
    Represents the metadata of a data lake bucket/container.
    Each bucket is associated with a unique name and a corresponding database name for storage.
    Auto-sync indicates that the bucket automatically loads files into the data lake and does not allow manual uploads.
    """

    meta = {
        "collection": "buckets",
        "strict": False,
        "indexes": [
            {"fields": ["bucket_name"], "unique": True},
            {"fields": ["db_name"], "unique": True},
        ],
    }
    bucket_name = StringField(required=True, unique=True)
    db_name = StringField(required=True)
    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    auto_sync = BooleanField(default=False)
    datalake_type = StringField(default="s3", choices=["s3", "azure"])
    # No static ``choices``: besides the platform IngestorType values, a custom deployment can register its
    # own ingestor via IngestorRegistry, and that set is not known at class-definition time. The create path
    # validates the value against IngestorRegistry; routing is exact-match, so an unknown value is simply
    # owned by no pipeline. The default stays the inert ``unassigned`` (see IngestorType).
    ingestor = StringField(required=True, default=IngestorType.UNASSIGNED.value)

    @staticmethod
    def _validate_name(name: str, field_name: str) -> None:
        if not name:
            raise ValidationError(f"{field_name} cannot be empty")

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", name):
            raise ValidationError(
                f"{field_name} '{name}' must start with a letter and contain only alphanumeric characters"
            )

    @classmethod
    def create_bucket(
        cls,
        bucket_name: str,
        db_name: str | None = None,
        name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
        auto_sync: bool = False,
        datalake_type: str = "s3",
        ingestor: str = IngestorType.UNASSIGNED.value,
        db_alias: str = "default",
    ) -> Self:
        cls._validate_name(bucket_name, "bucket_name")
        if db_name:
            cls._validate_name(db_name, "db_name")
        with switch_db(cls, db_alias) as SwitchedBucket:
            bucket = SwitchedBucket(
                id=ObjectId(),
                bucket_name=bucket_name,
                db_name=db_name or bucket_name,
                name=name or LocaleStringEntity(en=bucket_name, de=bucket_name, fr=bucket_name, it=bucket_name),
                description=description or LocaleStringEntity(),
                auto_sync=auto_sync,
                datalake_type=datalake_type,
                ingestor=ingestor,
            )
            bucket.save()
            return bucket

    @classmethod
    def get_bucket_by_id(cls, bucket_id: str, db_alias: str = "default") -> Self:
        with switch_db(cls, db_alias) as SwitchedBucket:
            return SwitchedBucket.objects().get(id=ObjectId(bucket_id))

    @classmethod
    def get_bucket_by_bucket_name(cls, bucket_name: str, db_alias: str = "default") -> Self:
        with switch_db(cls, db_alias) as SwitchedBucket:
            return SwitchedBucket.objects().get(bucket_name=bucket_name)

    @classmethod
    def get_bucket_by_db_name(cls, db_name: str, db_alias: str = "default") -> Self:
        with switch_db(cls, db_alias) as SwitchedBucket:
            return SwitchedBucket.objects().get(db_name=db_name)

    @classmethod
    def get_all_buckets(cls, db_alias: str = "default") -> list["BucketEntity"]:
        with switch_db(cls, db_alias) as SwitchedBucket:
            return SwitchedBucket.objects().order_by("bucket_name")

    @classmethod
    def update_bucket(
        cls,
        bucket_id: str,
        bucket_name: str | None = None,
        db_name: str | None = None,
        name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
        auto_sync: bool | None = None,
        datalake_type: str | None = None,
        ingestor: str | None = None,
        db_alias: str = "default",
    ) -> Self:
        bucket = cls.get_bucket_by_id(bucket_id, db_alias=db_alias)
        if bucket_name is not None:
            bucket.bucket_name = bucket_name
        if db_name:
            bucket.db_name = db_name
        if name:
            bucket.name = name
        if description:
            bucket.description = description
        if auto_sync is not None:
            bucket.auto_sync = auto_sync
        if datalake_type:
            bucket.datalake_type = datalake_type
        if ingestor is not None:
            bucket.ingestor = ingestor
        bucket.save()
        return bucket

    @classmethod
    def delete_bucket(cls, bucket_id: str, db_alias: str = "default") -> Self:
        bucket = cls.get_bucket_by_id(bucket_id, db_alias=db_alias)
        bucket.delete()
        return bucket
