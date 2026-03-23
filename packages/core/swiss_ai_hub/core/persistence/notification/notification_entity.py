from datetime import UTC, datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocumentField,
    StringField,
)

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity


class NotificationEntity(Document):
    """
    Represents a notification for a user in the database.
    """

    meta = {
        "collection": "notifications",
        "indexes": [
            {"fields": ["user_id"]},
            {"fields": ["user_id", "-created_at"]},
        ],
    }

    user_id = StringField(required=True)
    notification_group_id = StringField(default=None)
    title = EmbeddedDocumentField(LocaleStringEntity)
    message = EmbeddedDocumentField(LocaleStringEntity)
    read = BooleanField(default=False)
    done = BooleanField(default=False)
    type = StringField(choices=("info", "warn", "success", "error"), default="info")
    severity = StringField(choices=("low", "medium", "high", "critical"), default="medium")
    link = StringField()
    created_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_for_user(
        cls,
        user_id: str,
        page: int,
        page_size: int,
        types: list[str] | None = None,
        severities: list[str] | None = None,
        read: bool | None = None,
        done: bool | None = None,
        order_by: str = "-created_at",
    ) -> tuple[list["NotificationEntity"], int]:
        """Retrieves a paginated list of notifications, with optional filters."""
        query = cls.objects(user_id=user_id)

        if types:
            query = query.filter(type__in=types)
        if severities:
            query = query.filter(severity__in=severities)
        if read is not None:
            query = query.filter(read=read)
        if done is not None:
            query = query.filter(done=done)

        offset = (page - 1) * page_size
        notifications = query.order_by(order_by).skip(offset).limit(page_size).all()
        total = query.count()
        return notifications, total

    @trace_fn
    def mark_as_read(self):
        self.read = True
        self.save()
        return self

    @trace_fn
    def mark_as_done(self):
        self.done = True
        self.save()
        return self

    @classmethod
    @trace_fn
    def mark_multiple_as_read(cls, user_id: str, notification_ids: list[str]) -> int:
        return cls.objects(id__in=notification_ids, user_id=user_id).update(set__read=True)

    @classmethod
    @trace_fn
    def mark_multiple_as_done(cls, user_id: str, notification_ids: list[str]) -> int:
        return cls.objects(id__in=notification_ids, user_id=user_id).update(set__done=True)
