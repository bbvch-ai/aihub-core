from typing import ClassVar

from mongoengine import DoesNotExist

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


class KnowledgeVisibility:
    """Which knowledge databases the platform offers to anyone at all, before per-user access rules apply.

    The knowledge page, the knowledge API and the collections chat clients list all ask here, so a database hidden in
    one place is hidden in every other.
    """

    SYSTEM_DATABASE_NAMES: ClassVar[frozenset[str]] = frozenset({"admin", "local", "config"})

    @staticmethod
    def is_legacy(bucket: BucketEntity) -> bool:
        """Whether the bucket belongs to a legacy deploy-bound pipeline (``default_rag`` / ``shared_rag``)."""
        return bucket.ingestor in (IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value)

    @classmethod
    def non_browsable_database_names(cls) -> frozenset[str]:
        """Names no caller may read from or delete in, whatever access rules they hold.

        Reserving a name for creation is not a reason to refuse reads of the database already on it, so the
        legacy names appear here only when the deployment hides legacy knowledge, making hidden mean
        unreadable rather than merely unlisted. Uploads and namespace creation stay open either way.
        """
        # Keyed on the two configured names, while the knowledge page hides by the bucket's ingestor. The two
        # agree unless a deployment renamed its buckets after seeding, which would leave such a bucket
        # unlisted yet readable by name; closing that would cost a bucket lookup on every guarded read.
        aihub_settings = AIHubSettings()
        system_names = cls.SYSTEM_DATABASE_NAMES | {aihub_settings.MONGO_MAIN_DB_NAME}
        if aihub_settings.SHOW_LEGACY_KNOWLEDGE:
            return frozenset(system_names)
        return frozenset(system_names | {aihub_settings.DEFAULT_BUCKET_NAME, aihub_settings.SHARED_BUCKET_NAME})

    @classmethod
    def is_browsable(cls, bucket: BucketEntity) -> bool:
        """Whether the database is offered at all: neither closed by name nor a legacy one the deployment hides."""
        if bucket.db_name in cls.non_browsable_database_names():
            return False
        return AIHubSettings().SHOW_LEGACY_KNOWLEDGE or not cls.is_legacy(bucket)

    @classmethod
    def is_browsable_database(cls, database: str) -> bool:
        """`is_browsable` by the database's name; a database that no longer exists is offered to nobody."""
        try:
            return cls.is_browsable(BucketEntity.get_bucket_by_db_name(database))
        except DoesNotExist:
            return False
