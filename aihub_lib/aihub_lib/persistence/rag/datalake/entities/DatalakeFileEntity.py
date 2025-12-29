import time
from enum import Enum

from bson import ObjectId
from mongoengine import Document, EnumField, IntField, NotUniqueError, StringField


class DatalakeFileStatus(str, Enum):
    PROCESSING = "processing"
    INGESTED = "ingested"


class DatalakeFileEntity(Document):
    """Tracks all files in the datalake for efficient querying instead of S3 listing."""

    meta = {
        "collection": "datalake_files",
        "strict": False,
        "indexes": [
            {"fields": ["bucket_id", "namespace_name", "-updated_at"]},
            {"fields": ["bucket_id", "namespace_name", "status", "-updated_at"]},
            {"fields": ["bucket_id", "namespace_name", "file_path"], "unique": True},
        ],
    }

    bucket_id = StringField(required=True)
    namespace_name = StringField(required=True)
    file_path = StringField(required=True)
    status = EnumField(DatalakeFileStatus, default=DatalakeFileStatus.PROCESSING)
    created_at = IntField(required=True)
    updated_at = IntField(required=True)

    @property
    def filename(self) -> str:
        if not self.file_path:
            return ""
        return self.file_path.split("/")[-1]

    @classmethod
    def create_file(cls, bucket_id: str, namespace_name: str, file_path: str) -> "DatalakeFileEntity":
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")
        current_time = int(time.time())
        file_entity = cls(
            id=ObjectId(),
            bucket_id=bucket_id,
            namespace_name=namespace_name,
            file_path=file_path,
            status=DatalakeFileStatus.PROCESSING,
            created_at=current_time,
            updated_at=current_time,
        )
        file_entity.save()
        return file_entity

    @classmethod
    def get_or_create_file(cls, bucket_id: str, namespace_name: str, file_path: str) -> "DatalakeFileEntity":
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")
        try:
            existing = cls.get_file_by_path(bucket_id, namespace_name, file_path)
            existing.status = DatalakeFileStatus.PROCESSING
            existing.updated_at = int(time.time())
            existing.save()
            return existing
        except cls.DoesNotExist:
            try:
                return cls.create_file(bucket_id=bucket_id, namespace_name=namespace_name, file_path=file_path)
            except NotUniqueError:
                # Race condition: another request created the file, fetch and update it
                existing = cls.get_file_by_path(bucket_id, namespace_name, file_path)
                existing.status = DatalakeFileStatus.PROCESSING
                existing.updated_at = int(time.time())
                existing.save()
                return existing

    @classmethod
    def get_file_by_path(cls, bucket_id: str, namespace_name: str, file_path: str) -> "DatalakeFileEntity":
        return cls.objects().get(bucket_id=bucket_id, namespace_name=namespace_name, file_path=file_path)

    @classmethod
    def get_files_by_namespace(
        cls, bucket_id: str, namespace_name: str, skip: int = 0, limit: int = 100
    ) -> list["DatalakeFileEntity"]:
        return list(
            cls.objects()
            .filter(bucket_id=bucket_id, namespace_name=namespace_name)
            .order_by("-updated_at")
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    def get_processing_files_by_namespace(
        cls, bucket_id: str, namespace_name: str, skip: int = 0, limit: int = 100
    ) -> list["DatalakeFileEntity"]:
        return list(
            cls.objects()
            .filter(bucket_id=bucket_id, namespace_name=namespace_name, status=DatalakeFileStatus.PROCESSING)
            .order_by("-updated_at")
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    def count_by_namespace(cls, bucket_id: str, namespace_name: str) -> int:
        return cls.objects().filter(bucket_id=bucket_id, namespace_name=namespace_name).count()

    @classmethod
    def count_processing_by_namespace(cls, bucket_id: str, namespace_name: str) -> int:
        return (
            cls.objects()
            .filter(bucket_id=bucket_id, namespace_name=namespace_name, status=DatalakeFileStatus.PROCESSING)
            .count()
        )

    def mark_ingested(self) -> "DatalakeFileEntity":
        self.status = DatalakeFileStatus.INGESTED
        self.updated_at = int(time.time())
        self.save()
        return self

    @classmethod
    def delete_by_path(cls, bucket_id: str, namespace_name: str, file_path: str) -> bool:
        try:
            file_entity = cls.get_file_by_path(bucket_id, namespace_name, file_path)
            file_entity.delete()
            return True
        except cls.DoesNotExist:
            return False
