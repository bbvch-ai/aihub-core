from bson import ObjectId
from mongoengine import Document, StringField, BooleanField, EmbeddedDocumentField

from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class BucketEntity(Document):
    meta = {
        "collection": "datalake_buckets",
        "strict": False,
        "indexes": [
            {"fields": ["bucket_name"], "unique": True},
        ],
    }
    bucket_name = StringField(required=True, unique=True)
    db_name = StringField(required=True)
    name = EmbeddedDocumentField(LocaleStringEntity, required=False)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
    automatic = BooleanField(default=False)

    @classmethod
    def create_bucket(
        cls,
        bucket_name: str,
        db_name: str | None = None,
        name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
        automatic: bool = False,
        bucket_id: ObjectId | None = None,
    ) -> "BucketEntity":
        bucket = cls(
            id=bucket_id or ObjectId(),
            bucket_name=bucket_name,
            db_name=db_name or bucket_name,
            name=name,
            description=description,
            automatic=automatic,
        )
        bucket.save()
        return bucket

    @classmethod
    def get_bucket_by_id(cls, bucket_id: str) -> "BucketEntity":
        return cls.objects().get(id=ObjectId(bucket_id))

    @classmethod
    def get_bucket_by_bucket_name(cls, bucket_name: str) -> "BucketEntity":
        return cls.objects().get(bucket_name=bucket_name)

    @classmethod
    def get_all_buckets(cls) -> list["BucketEntity"]:
        return cls.objects().order_by("bucket_name")

    @classmethod
    def update_bucket(
        cls,
        bucket_id: str,
        bucket_name: str | None = None,
        db_name: str | None = None,
        name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
        automatic: bool | None = None,
    ) -> "BucketEntity":
        bucket = cls.get_bucket_by_id(bucket_id)
        if bucket_name is not None:
            bucket.bucket_name = bucket_name
        if db_name:
            bucket.db_name = db_name
        if name:
            bucket.name = name
        if description:
            bucket.description = description
        if automatic:
            bucket.automatic = automatic
        bucket.save()
        return bucket

    @classmethod
    def delete_bucket(cls, bucket_id: str) -> "BucketEntity":
        bucket = cls.get_bucket_by_id(bucket_id)
        bucket.delete()
        return bucket
