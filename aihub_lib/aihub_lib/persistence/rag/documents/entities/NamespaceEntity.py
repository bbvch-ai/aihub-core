import time
from bson import ObjectId
from mongoengine import Document, StringField, EmbeddedDocumentField, IntField

from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class NamespaceEntity(Document):
    meta = {
        "collection": "namespaces",
        "strict": False,
        "indexes": [
            {"fields": ["bucket_id", "namespace_name"], "unique": True},
            {"fields": ["bucket_id"]},
        ],
    }
    bucket_id = StringField(required=True)
    namespace_name = StringField(required=True)
    folder_name = StringField(required=True)
    display_name = EmbeddedDocumentField(LocaleStringEntity, required=False)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
    created_at = IntField(required=True)
    last_updated = IntField(required=True)
    inserted_at = IntField(required=True)

    @classmethod
    def create_namespace(
        cls,
        bucket_id: str,
        namespace_name: str,
        folder_name: str | None = None,
        display_name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
        namespace_id: ObjectId | None = None,
    ) -> "NamespaceEntity":
        current_time = int(time.time())
        namespace = cls(
            id=namespace_id or ObjectId(),
            bucket_id=bucket_id,
            namespace_name=namespace_name,
            folder_name=folder_name or namespace_name,
            display_name=display_name,
            description=description,
            created_at=current_time,
            last_updated=current_time,
            inserted_at=current_time,
        )
        namespace.save()
        return namespace

    @classmethod
    def get_namespace_by_id(cls, namespace_id: str) -> "NamespaceEntity":
        return cls.objects().get(id=ObjectId(namespace_id))

    @classmethod
    def get_namespace_by_bucket_and_name(cls, bucket_id: str, namespace_name: str) -> "NamespaceEntity":
        return cls.objects().get(bucket_id=bucket_id, namespace_name=namespace_name)

    @classmethod
    def get_namespaces_by_bucket(cls, bucket_id: str) -> list["NamespaceEntity"]:
        return cls.objects().filter(bucket_id=bucket_id).order_by("namespace_name")

    @classmethod
    def get_all_namespaces(cls) -> list["NamespaceEntity"]:
        return cls.objects().order_by("bucket_id", "namespace_name")

    @classmethod
    def update_namespace(
        cls,
        namespace_id: str,
        namespace_name: str | None = None,
        folder_name: str | None = None,
        display_name: LocaleStringEntity | None = None,
        description: LocaleStringEntity | None = None,
    ) -> "NamespaceEntity":
        namespace = cls.get_namespace_by_id(namespace_id)
        if namespace_name:
            namespace.namespace_name = namespace_name
        if folder_name:
            namespace.folder_name = folder_name
        if display_name:
            namespace.display_name = display_name
        if description:
            namespace.description = description
        namespace.last_updated = int(time.time())
        namespace.save()
        return namespace

    @classmethod
    def delete_namespace(cls, namespace_id: str) -> "NamespaceEntity":
        namespace = cls.get_namespace_by_id(namespace_id)
        namespace.delete()
        return namespace
