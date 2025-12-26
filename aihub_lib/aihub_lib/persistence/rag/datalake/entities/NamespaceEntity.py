import re
import time

from bson import ObjectId
from mongoengine import Document, EmbeddedDocumentField, IntField, StringField, ValidationError

from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class NamespaceEntity(Document):
    """
    Represents a folder or namespace within a data lake bucket/container.
    Each namespace is uniquely identified by its name within the context of a specific bucket.
    Each namespace has a corresponding folder name in the data lake.
    """

    meta = {
        "collection": "namespaces",
        "strict": False,
        "indexes": [
            {"fields": ["bucket_id", "namespace_name"], "unique": True},
            {"fields": ["bucket_id"]},
            {"fields": ["bucket_id", "folder_name"]},
        ],
    }
    bucket_id = StringField(required=True)
    namespace_name = StringField(required=True)
    folder_name = StringField(required=True)
    display_name = EmbeddedDocumentField(LocaleStringEntity, required=False)
    description = EmbeddedDocumentField(LocaleStringEntity, required=False)
    created_at = IntField(required=True)
    updated_at = IntField(required=True)
    inserted_at = IntField(required=True)

    @staticmethod
    def _validate_namespace_name(name: str) -> None:
        if not name:
            raise ValidationError("namespace_name cannot be empty")
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValidationError("namespace_name can only contain alphanumeric characters, hyphens, and underscores")

    @staticmethod
    def _validate_folder_name(name: str) -> None:
        if not name:
            raise ValidationError("folder_name cannot be empty")

    @staticmethod
    def _sanitize_namespace_name(name: str) -> str:
        """Sanitize namespace name to only contain alphanumeric, hyphens, and underscores."""
        return re.sub(r"[^a-zA-Z0-9_-]", "_", name)

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
        sanitized_namespace_name = cls._sanitize_namespace_name(namespace_name)
        cls._validate_namespace_name(sanitized_namespace_name)

        resolved_folder_name = folder_name or namespace_name
        cls._validate_folder_name(resolved_folder_name)

        current_time = int(time.time())
        namespace = cls(
            id=namespace_id or ObjectId(),
            bucket_id=bucket_id,
            namespace_name=sanitized_namespace_name,
            folder_name=resolved_folder_name,
            display_name=display_name,
            description=description,
            created_at=current_time,
            updated_at=current_time,
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
    def get_namespace_by_bucket_and_folder(cls, bucket_id: str, folder_name: str) -> "NamespaceEntity":
        return cls.objects().get(bucket_id=bucket_id, folder_name=folder_name)

    @classmethod
    def get_namespaces_by_bucket(cls, bucket_id: str) -> list["NamespaceEntity"]:
        return (
            cls.objects()
            .filter(
                bucket_id=bucket_id,
            )
            .order_by("namespace_name")
        )

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
            sanitized_namespace_name = cls._sanitize_namespace_name(namespace_name)
            cls._validate_namespace_name(sanitized_namespace_name)
            namespace.namespace_name = sanitized_namespace_name
        if folder_name:
            cls._validate_folder_name(folder_name)
            namespace.folder_name = folder_name
        if display_name:
            namespace.display_name = display_name
        if description:
            namespace.description = description
        namespace.updated_at = int(time.time())
        namespace.save()
        return namespace

    @classmethod
    def delete_namespace(cls, namespace_id: str) -> "NamespaceEntity":
        namespace = cls.get_namespace_by_id(namespace_id)
        namespace.delete()
        return namespace
