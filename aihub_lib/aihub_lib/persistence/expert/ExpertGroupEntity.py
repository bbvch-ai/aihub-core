from __future__ import annotations

from datetime import UTC, datetime

from mongoengine import DateTimeField, Document, ListField, StringField

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class ExpertGroupEntity(Document):
    """
    Represents an expert group in the system.

    Expert groups define collections of users who can receive and answer
    expert questions in the Expert-in-the-Loop workflow.
    """

    DEFAULT_GROUP_NAME = "defaultexpertgroup"

    meta = {
        "collection": "expert_groups",
        "strict": False,
        "indexes": [
            {"fields": ["name"], "unique": True},
        ],
    }

    name = StringField(required=True, unique=True)
    description = StringField()
    member_user_ids = ListField(StringField(), default=list)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_by_name(cls, name: str) -> ExpertGroupEntity | None:
        """Fetches an expert group by its name. Returns None if not found."""
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def get_member_user_ids(cls, group_name: str) -> list[str]:
        """Returns the list of member user IDs for a group. Empty list if group not found."""
        group = cls.objects(name=group_name).first()
        return list(group.member_user_ids) if group else []

    @classmethod
    @trace_fn
    def list_all(cls) -> list[ExpertGroupEntity]:
        """Lists all expert groups."""
        return list(cls.objects())

    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)
        return super().save(*args, **kwargs)
