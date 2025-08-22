from mongoengine import Document as MongoDocument
from mongoengine import IntField

from aihub_lib.persistence.base.schema_version import CURRENT_SCHEMA_VERSION


class VersionedDocument(MongoDocument):
    """
    Base document class that includes schema versioning.

    All documents in the AI-Hub should inherit from this class
    to ensure consistent schema versioning across the system.
    """

    meta = {
        "abstract": True,
        "strict": True,
    }

    schema_version = IntField(default=CURRENT_SCHEMA_VERSION, required=True)

    @classmethod
    def get_current_schema_version(cls) -> int:
        """Get the current schema version for this document class."""
        return CURRENT_SCHEMA_VERSION

    @classmethod
    def get_documents_by_version(cls, version: int):
        """Query documents by schema version."""
        return cls.objects(schema_version=version)

    @classmethod
    def count_by_version(cls) -> dict[int, int]:
        """Get count of documents grouped by schema version."""
        pipeline = [
            {"$group": {"_id": "$schema_version", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        results = cls.objects.aggregate(pipeline)
        return {r["_id"]: r["count"] for r in results}
