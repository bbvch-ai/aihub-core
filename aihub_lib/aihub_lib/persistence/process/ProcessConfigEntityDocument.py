from datetime import UTC, datetime

from mongoengine import DateTimeField, Document

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.process import ProcessConfigEntity


class ProcessConfigEntityDocument(ProcessConfigEntity, Document):
    """
    This is the specific class for storing process configurations in the `process_configs` collection.
    It extends the base `ProcessConfigEntity` class and uses MongoDB's Document model for persistence as
    a standalone collection.
    This is commonly used to store specific configurations defined in the MongoDB database by the user.
    """

    meta = {
        "collection": "process_configs",
        "indexes": [
            {"fields": ("process_class", "process_id"), "unique": True},
            {"fields": ["process_class"]},
        ],
    }

    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def find_for_class(cls, process_class: str) -> list["ProcessConfigEntityDocument"]:
        """Find all configurations for a specific process class."""
        return cls.objects(process_class=process_class)

    @classmethod
    @trace_fn
    def find_for_class_and_id(cls, process_class: str, process_id: str) -> "ProcessConfigEntityDocument | None":
        """Find a specific configuration by process class and ID."""
        return cls.objects(process_class=process_class, process_id=process_id).first()

    @classmethod
    @trace_fn
    def delete_if_exists_for_class_and_id(cls, process_class: str, process_id: str) -> None:
        """Delete a specific configuration by process class and ID if it exists."""
        existing = cls.find_for_class_and_id(process_class, process_id)
        if existing:
            existing.delete()

    @trace_fn
    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)
        return super().save(*args, **kwargs)
